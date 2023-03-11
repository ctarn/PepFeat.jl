module PepFeatAlign

import ArgParse
import CSV
import DataFrames
import MesCore
import ProgressMeter: @showprogress

align_feature(path, args) = begin
    l = parse(Float64, args["l"])
    ε_m = parse(Float64, args["m"]) * 1e-6
    ε_t = parse(Float64, args["t"])
    α = parse(Float64, args["f"])
    @info "feature list loading from " * path
    df = path |> CSV.File |> DataFrames.DataFrame
    DataFrames.sort!(df, :rtime)
    @info "reference loading from " * args["ref"]
    df_ref = args["ref"] |> CSV.File |> DataFrames.DataFrame
    df_ref = df_ref[df_ref.rtime_len .≥ l, :]
    DataFrames.sort!(df_ref, :mz)
    df.matched .= false
    df.match_id .= 0
    df.rtime_aligned .= Inf
    df.delta_rt .= Inf
    df.delta_rt_aligned .= Inf
    df.delta_mz .= Inf
    df.delta_abu .= Inf
    softer = MesCore.exp_softer(parse(Float64, args["s"]))
    Δ = 0.0
    @showprogress for a in eachrow(df)
        a.rtime_aligned = a.rtime + Δ
        if a.rtime_len < l continue end
        idx = filter(MesCore.argquery_ε(df_ref.mz, a.mz, ε_m)) do i
            df_ref[i, :z] == a.z && abs(df_ref[i, :rtime] - a.rtime_aligned) ≤ ε_t
        end
        if length(idx) == 0 continue end
        _, i = findmin(x -> abs(df_ref[x, :rtime] - a.rtime_aligned), idx)
        b = df_ref[idx[i], :]
        δ = b.rtime - a.rtime
        Δ += α * softer(δ - Δ)
        a.matched = true
        a.match_id = b.id # may not equal to `i`
        a.delta_rt = δ
        a.delta_rt_aligned = b.rtime - a.rtime_aligned
        a.delta_mz = MesCore.error_ppm(a.mz, b.mz)
        a.delta_abu = b.inten_apex / a.inten_apex
    end
    mkpath(args["o"])
    path_out = joinpath(args["o"], splitext(basename(path))[1] * "_aligned.csv")
    @info "saving to " * path_out * "~"
    CSV.write(path_out * "~", df)
    mv(path_out * "~", path_out; force=true)
    @info "saved to " * path_out

    df_shift = DataFrames.DataFrame(time=df.rtime, shift=df.rtime_aligned .- df.rtime)[df.matched, :]
    path_out = joinpath(args["o"], splitext(basename(path))[1] * "_shift.csv")
    @info "saving to " * path_out * "~"
    CSV.write(path_out * "~", df_shift)
    mv(path_out * "~", path_out; force=true)
    @info "saved to " * path_out
end

main() = begin
    settings = ArgParse.ArgParseSettings(prog="PepFeatAlign")
    ArgParse.@add_arg_table! settings begin
        "-f"
            help = "moving average factor"
            metavar = "factor"
            default = "0.1"
        "-s"
            help = "moving average scale"
            metavar = "scale"
            default = "64"
        "-m"
            help = "m/z error"
            metavar = "ppm"
            default = "1.0"
        "-t"
            help = "max retention time error"
            metavar = "second"
            default = "600.0"
        "-l"
            help = "min retention time length"
            metavar = "second"
            default = "4.0"
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
    for path in args["data"], file in readdir(dirname(path))
        if file == basename(path) || (startswith(file, basename(path)) && endswith(file, ".csv"))
            align_feature(joinpath(dirname(path), file), args)
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
