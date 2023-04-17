module PepFeatDetect

using Base: Filesystem
using Distributed
using Statistics

import ArgParse
import CSV
import MesMS
import MesMS: PepIso
import ProgressMeter: @showprogress

check_iso(ion, spec, ε, V) = map(m -> !isempty(MesMS.query_ε(spec, ion.mz + m / ion.z, ε)), MesMS.ipv_m(ion, V))

build_feature(ions, ε, V) = begin
    apex = argmax(i -> i.x, ions)
    # mass
    mz = sum(i -> i.mz * i.x, ions) / sum(i -> i.x, ions)
    z = ions[begin].z
    mh = MesMS.mz_to_mh(mz, z)
    mz_max = MesMS.ipv_m(mz * z, V)[argmax(MesMS.ipv_w(apex, V))] / z + mz
    # retention time
    rtime, _ = MesMS.calc_centroid(map(i -> i.ms.retention_time, ions), map(i -> i.x, ions))
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
    inten_window = sum(p -> p.inten, MesMS.query(apex.ms.peaks, (1 - 2ε) * apex.mz, (1 + 2ε) * MesMS.ipv_mz(apex, iso_last_apex, V)))
    inten_rate = apex.x / inten_window
    return (; mh, mz, z, mz_max,
        rtime, rtime_start, rtime_stop, rtime_len, rtime_apex, fwhm, scan_start, scan_stop, scan_num, scan_apex,
        inten_apex, inten_sum, inten_rate, inten_window, iso_shape_apex, iso_shape_mean,
        iso_apex_str, iso_num_apex, iso_last_apex, iso_num_max, iso_last_max, iso_str, iso_num, iso_last,
    )
end

prepare(args) = begin
    max_n = parse(Int, args["p"])
    zs = Vector{Int}(MesMS.parse_range(Int, args["z"]))
    τ = parse(Float64, args["t"])
    ε = parse(Float64, args["e"]) * 1.0e-6
    V = MesMS.build_ipv(args["m"])
    gap = parse(Int, args["g"])
    addprocs(parse(Int, args["proc"]))
    @eval @everywhere using PepFeat.PepFeatDetect
    out = mkpath(args["o"])
    return (; max_n, zs, τ, ε, V, gap, out)
end

detect_feature(fname; max_n, zs, τ, ε, V, gap, out) = begin
    @info "loading from " * fname
    M = MesMS.read_ms1(fname)
    @info "deisotoping"
    I = @showprogress pmap(M) do m
        peaks = MesMS.pick_by_inten(m.peaks, max_n)
        ions = [MesMS.Ion(p.mz, z) for p in peaks for z in zs]
        ions = filter(i -> i.mz * i.z < length(V) && PepIso.prefilter(i, peaks, ε, V), ions)
        ions = PepIso.deisotope(ions, peaks, τ, ε, V; split=true)
        ions = [(; ion..., ms=m) for ion in ions]
    end
    G = PepIso.group_ions(I, gap, ε)
    d = Dict{Int, Int}()
    foreach(l -> d[l] = get(d, l, 0) + 1, map(length, G))
    foreach(k -> println("$(k)\t$(get(d, k, 0))"), minimum(keys(d)):100)
    @info "analysing"
    F = @showprogress map(G) do ions
        build_feature(ions, ε, V)
    end
    F = [(; id=i, f...) for (i, f) in enumerate(F)]
    path = joinpath(out, splitext(basename(fname))[1] * ".feature.csv")
    @info "result saving to " * path
    CSV.write(path, F)
end

main() = begin
    settings = ArgParse.ArgParseSettings(prog="PepFeatDetect")
    ArgParse.@add_arg_table! settings begin
        "--proc"
            help = "number of additional worker processes"
            metavar = "n"
            default = "4"
        "-m"
            help = "model file"
            metavar = "model"
            default = joinpath(homedir(), ".MesMS/IPV.bson")
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
    sess = prepare(args)
    for path in args["data"], file in readdir(dirname(path))
        if file == basename(path) || (startswith(file, basename(path)) && endswith(file, ".ms1"))
            detect_feature(joinpath(dirname(path), file); sess...)
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
