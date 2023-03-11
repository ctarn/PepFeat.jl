module PepFeat

include("PepFeatDetect.jl")
include("PepFeatAlign.jl")

main_PepFeatDetect()::Cint = PepFeatDetect.julia_main()
main_PepFeatAlign()::Cint = PepFeatDetect.julia_main()

end
