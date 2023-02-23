module PepFeat

using Base: Filesystem
using Distributed
using Statistics

import ArgParse
import CSV
import Graphs
import MesCore
import PepIso: PepIso, IPV
import ProgressMeter: @showprogress

split_ions(ions, spec, ε, V) = begin
    items = [(; i, n, mz=IPV.ipv_mz(ion, n, V)) for (i, ion) in enumerate(ions) for n in eachindex(IPV.ipv_w(ion, V))]
    cs = map(p -> (; p.mz, p.inten, slots=empty(items)), spec)
    for i in items
        l, r = searchsortedfirst(spec, (1 - ε) * i.mz), searchsortedlast(spec, (1 + ε) * i.mz)
        εs = map(p -> abs(i.mz - p.mz), spec[l:r])
        l <= r && push!(cs[argmin(εs)+l-1].slots, i)
    end
    cs = filter(c -> !isempty(c.slots), cs)
    g = Graphs.SimpleGraph(length(ions))
    for c in cs
        a = c.slots[begin]
        for b in c.slots[begin+1:end]
            Graphs.add_edge!(g, a.i, b.i)
        end
    end
    coms = Graphs.connected_components(g)
    tab = zeros(Int, length(ions))
    for (i, com) in enumerate(coms)
        tab[com] .= i
    end
    slices = map(_ -> MesCore.Peak[], coms)
    for c in cs
        push!(slices[tab[c.slots[begin].i]], MesCore.Peak(c.mz, c.inten))
    end
    return map(idxs -> ions[idxs], coms), slices
end

split_and_evaluate(ions, spec, τ_max, ε, V) = begin
    scores = map(zip(split_ions(ions, spec, ε, V)...)) do (ions_sub, spec_sub)
        return PepIso.deisotope(ions_sub, spec_sub, τ_max, ε, V)
    end
    return reduce(vcat, scores)
end

check_iso(ion, spec, ε, V) = map(m -> !isempty(MesCore.query_ε(spec, ion.mz + m / ion.z, ε)), IPV.ipv_m(ion, V))

build_feature(ions, ε, V) = begin
    apex = argmax(i -> i.x, ions)
    # mass
    mz = sum(i -> i.mz * i.x, ions) / sum(i -> i.x, ions)
    z = ions[begin].z
    mh = MesCore.mz_to_mh(mz, z)
    mz_max = IPV.ipv_m(mz * z, V)[argmax(IPV.ipv_w(apex, V))] / z + mz
    # retention time
    rtime, _ = MesCore.calc_centroid(map(i -> i.ms.retention_time, ions), map(i -> i.x, ions))
    rtime_start, rtime_stop = extrema(i -> i.ms.retention_time, ions)
    rtime_len = rtime_stop - rtime_start
    rtime_apex = apex.ms.retention_time
    half = map(i -> i.x * 2 > apex.x, ions)
    fwhm = ions[findlast(half)].ms.retention_time - ions[findfirst(half)].ms.retention_time
    # scan
    scan_start, scan_stop = extrema(i -> i.ms.id, ions)
    scan_num = length(ions)
    scan_apex = apex.ms.id
    # intensity
    inten_sum = sum(i -> i.x, ions)
    inten_apex = apex.x
    # isotope
    iso_shape_apex = apex.m
    iso_shape_mean = mean(i -> i.m, ions)
    iso_apex = check_iso(apex, apex.ms.peaks, ε, V)
    iso_num_apex = sum(iso_apex)
    iso_last_apex = findlast(iso_apex)
    iso_apex_str = join(Int.(iso_apex[begin:findlast(iso_apex)]))
    iso = map(i -> check_iso(i, i.ms.peaks, ε, V), ions)
    iso_str = map(i -> join(Int.(i[begin:findlast(i)])), iso)
    iso_num = map(sum, iso)
    iso_num_max = maximum(iso_num)
    iso_last = map(findlast, iso)
    iso_last_max = maximum(iso_last)
    # precursor ion fraction
    inten_window = sum(p -> p.inten, MesCore.query(apex.ms.peaks, (1 - 2ε) * apex.mz, (1 + 2ε) * IPV.ipv_mz(apex, iso_last_apex, V)))
    inten_rate = apex.x / inten_window
    return (; mh, mz, z, mz_max,
        rtime, rtime_start, rtime_stop, rtime_len, rtime_apex, fwhm, scan_start, scan_stop, scan_num, scan_apex,
        inten_apex, inten_sum, inten_rate, inten_window, iso_shape_apex, iso_shape_mean,
        iso_apex_str, iso_num_apex, iso_last_apex, iso_num_max, iso_last_max, iso_str, iso_num, iso_last,
    )
end

detect_feature(fname, args) = begin
    τ_exclusion = parse(Float64, args["t"])
    ε = parse(Float64, args["e"]) * 1.0e-6
    gap = parse(Int, args["g"])
    zs = Vector{Int}(MesCore.parse_range(Int, args["z"]))
    max_n = parse(Int, args["p"])

    V = IPV.build_ipv(args["m"])

    @info "loading from " * fname
    M = MesCore.read_ms1(fname)
    @info "deisotoping"
    addprocs(parse(Int, args["proc"]))
    @eval @everywhere using PepFeat
    I = @showprogress pmap(M) do m
        peaks = MesCore.pick_by_inten(m.peaks, max_n)
        ions = [MesCore.Ion(p.mz, z) for p in peaks for z in zs]
        ions = filter(i -> i.mz * i.z < length(V) && PepIso.prefilter(i, peaks, ε, V), ions)
        ions = split_and_evaluate(ions, peaks, τ_exclusion, ε, V)
        ions = [(; ion..., ms=m) for ion in ions]
    end
    G = []
    for z in zs
        @info "grouping (charge state: $(z))"
        tmp = []
        gs = ones(Int, length(tmp))
        @showprogress for ions in I
            s = gs .> gap
            append!(G, tmp[s])
            tmp, gs = tmp[.!s], gs[.!s]
            for ion in filter(i -> i.z == z, ions)
                grouped = false
                for (j, t) in enumerate(tmp)
                    if MesCore.in_moe(ion.mz, t[end].mz, ε)
                        push!(t, ion)
                        grouped = true
                        gs[j] = 0
                        break
                    end
                end
                if !grouped
                    push!(tmp, [ion])
                    push!(gs, 0)
                end
            end
            gs .+= 1
        end
        append!(G, tmp)
    end
    d = Dict{Int, Int}()
    foreach(l -> d[l] = get(d, l, 0) + 1, map(length, G))
    foreach(k -> println("$(k)\t$(get(d, k, 0))"), minimum(keys(d)):100)
    @info "analysing"
    F = @showprogress map(G) do ions
        build_feature(ions, ε, V)
    end
    F = [(; id=i, f...) for (i, f) in enumerate(F)]
    mkpath(args["o"])
    path = joinpath(args["o"], splitext(basename(fname))[1] * ".feature.csv")
    @info "result saving to " * path
    CSV.write(path, F)
end

main() = begin
    settings = ArgParse.ArgParseSettings(prog="PepFeat")
    ArgParse.@add_arg_table! settings begin
        "--proc"
            help = "number of additional worker processes"
            metavar = "n"
            default = "4"
        "-m"
            help = "model file"
            metavar = "model"
            default = joinpath(homedir(), ".PepFeat/IPV.bson")
        "-t"
            help = "exclusion threshold"
            metavar = "threshold"
            default = "1.0"
        "-e"
            help = "m/z error"
            metavar = "ppm"
            default = "10.0"
        "-g"
            help = "scan gap"
            metavar = "gap"
            default = "16"
        "-p"
            help = "max #peak per scan"
            metavar = "num"
            default = "4000"
        "-z"
            help = "charge states"
            metavar = "min:max"
            default = "2:6"
        "-o"
            help = "output directory"
            metavar = "output"
            default = "./out/"
        "data"
            help = "list of .ms1 files"
            nargs = '+'
            required = true
    end
    args = ArgParse.parse_args(settings)
    for path in args["data"]
        for file in readdir(dirname(path))
            if startswith(file, basename(path)) && endswith(file, ".ms1")
                detect_feature(joinpath(dirname(path), file), args)
            end
        end
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

julia_main()::Cint = begin
    main()
    return 0
end

end
