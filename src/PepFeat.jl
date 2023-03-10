module PepFeat

include("PepFeatDetect.jl")

main_PepFeatDetect()::Cint = PepFeatDetect.julia_main()

end
