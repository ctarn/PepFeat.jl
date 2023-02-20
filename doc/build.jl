import LibGit2

import Documenter

repo = "github.com/ctarn/PepFeat.jl.git"

root = "doc"
out = joinpath("tmp", "doc")

rm(out; force=true, recursive=true)
LibGit2.clone("https://$(repo)", out, branch="gh-pages")
rm(joinpath(out, ".git"); force=true, recursive=true)

vs = readdir(joinpath(root, "log")) .|> VersionNumber
sort!(vs; rev=true)
logs = map(vs) do v in
    "<li> version $(v):<div>$(read(joinpath(root, "log", string(v)), String))</div></li>"
end

html = read(joinpath(root, "index.html"), String)
html = replace(html, "{{ release }}" => "<ul>$(join(logs))</ul>")
open(io -> write(io, html), joinpath(out, "index.html"); write=true)

open(io -> write(io, "pepfeat.ctarn.io"), joinpath(out, "CNAME"); write=true)

Documenter.deploydocs(repo=repo, target=joinpath("..", out), versions=nothing)

Documenter.makedocs(sitename="PepFeat", build=joinpath("..", out))
Documenter.deploydocs(repo=repo, target=joinpath("..", out), dirname="doc")
