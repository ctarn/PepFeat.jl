module PepFeatAlign

using Statistics

import ArgParse
import CSV
import DataFrames
import MesCore
import ProgressMeter: @showprogress

prepare(args) = begin
    len_rt = parse(Float64, args["l"])
    ε_m = parse(Float64, args["m"]) * 1e-6
    ε_t = parse(Float64, args["t"])
    bin_size = parse(Float64, args["b"])
    α = parse(Float64, args["f"])
    softer = MesCore.exp_softer(parse(Float64, args["s"]))
    @info "reference loading from " * args["ref"]
    df_ref = args["ref"] |> CSV.File |> DataFrames.DataFrame
    df_ref = df_ref[df_ref.rtime_len .≥ len_rt, :]
    DataFrames.sort!(df_ref, :mz)
    out = mkpath(args["o"])
    return (; df_ref, len_rt, ε_m, ε_t, bin_size, α, softer, out)
end

align_feature(path; df_ref, len_rt, ε_m, ε_t, bin_size, α, softer, out) = begin
    @info "feature list loading from " * path
    df = path |> CSV.File |> DataFrames.DataFrame
    df.matched .= false
    df.match_id .= 0
    df.rtime_aligned .= Inf
    df.delta_rt .= Inf
    df.delta_rt_aligned .= Inf
    df.delta_mz .= Inf
    df.delta_abu .= Inf
    df.bin = round.(Int, df.rtime ./ bin_size)
    bin_min, bin_max = extrema(df.bin)
    bins = [Int[] for _ in (bin_min-1):(bin_max+1)]
    Δs = zeros(length(bins))
    Δidx = bin_min - 2
    df.bin_idx = df.bin .- Δidx
    @showprogress for (i, idx) in enumerate(df.bin_idx)
        push!(bins[idx], i)
    end
    referable = trues(DataFrames.nrow(df_ref))
    @showprogress for i_b in 2:(length(bins)-1)
        δs = Float64[]
        for i_f in bins[i_b]
            a = df[i_f, :]
            a.rtime_aligned = a.rtime + Δs[i_b-1]
            if a.rtime_len < len_rt continue end
            idx = filter(MesCore.argquery_ε(df_ref.mz, a.mz, ε_m)) do i
                referable[i] && df_ref[i, :z] == a.z && abs(df_ref[i, :rtime] - a.rtime_aligned) ≤ ε_t
            end
            if isempty(idx) continue end
            _, i = findmin(x -> abs(df_ref[x, :rtime] - a.rtime_aligned), idx)
            referable[idx[i]] = false
            b = df_ref[idx[i], :]
            δ = b.rtime - a.rtime
            push!(δs, δ)
            a.matched = true
            a.match_id = b.id # may not equal to `i`
            a.delta_rt = δ
            a.delta_rt_aligned = b.rtime - a.rtime_aligned
            a.delta_mz = MesCore.error_ppm(a.mz, b.mz)
            a.delta_abu = b.inten_apex / a.inten_apex
        end
        Δs[i_b] = Δs[i_b-1] + (isempty(δs) ? 0 : α * mean(softer.(δs .- Δs[i_b-1])))
    end
    path_out = joinpath(out, splitext(basename(path))[1] * "_aligned.csv")
    @info "saving to " * path_out * "~"
    CSV.write(path_out * "~", df)
    mv(path_out * "~", path_out; force=true)
    @info "saved to " * path_out

    df_shift = DataFrames.DataFrame(time=Vector((bin_min:bin_max) * bin_size), shift=Δs[begin+1:end-1])
    path_out = joinpath(out, splitext(basename(path))[1] * "_shift.csv")
    @info "saving to " * path_out * "~"
    CSV.write(path_out * "~", df_shift)
    mv(path_out * "~", path_out; force=true)
    @info "saved to " * path_out
end

main() = begin
    settings = ArgParse.ArgParseSettings(prog="PepFeatAlign")
    ArgParse.@add_arg_table! settings begin
        "-l"
            help = "min retention time length"
            metavar = "second"
            default = "4.0"
        "-m"
            help = "m/z error"
            metavar = "ppm"
            default = "1.0"
        "-t"
            help = "max retention time error"
            metavar = "second"
            default = "600.0"
        "-b"
            help = "moving average step (or, bin size)"
            metavar = "second"
            default = "1.0"
        "-f"
            help = "moving average factor (or, updating rate)"
            metavar = "factor"
            default = "0.1"
        "-s"
            help = "moving average scale"
            metavar = "scale"
            default = "64"
        "-o"
            help = "output directory"
            metavar = "output"
            default = "./out/"
        "--ref", "--to"
            help = "referred feature list"
            metavar = "reference"
            required = true
        "data"
            help = "feature list"
            nargs = '+'
            required = true
    end
    args = ArgParse.parse_args(settings)
    sess = prepare(args)
    for path in args["data"], file in readdir(dirname(path))
        if file == basename(path) || (startswith(file, basename(path)) && endswith(file, ".csv"))
            align_feature(joinpath(dirname(path), file); sess...)
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
