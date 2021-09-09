
using Revise
using Rocket
using ReactiveMP
using GraphPPL
using Distributions
using LinearAlgebra
import ProgressMeter



@model function lar_model_univariate(order, c, stype)
    mx_prev = datavar(Float64)
    vx_prev = datavar(Float64)
    y = datavar(Float64)

    γ  ~ GammaShapeRate(1.0, 1.0) where { q = MeanField() }
    θ  ~ NormalMeanPrecision(0.0, 1.0) where { q = MeanField() }
    x_prev ~ NormalMeanPrecision(mx_prev, vx_prev) where { q = MeanField() }

    γ_y = constvar(1.0)

    meta = ARMeta(Univariate, order, stype)

    x ~ AR(x_prev, θ, γ) where { q = q(y, x_prev)q(γ)q(θ), meta = meta }
    y ~ NormalMeanPrecision(x, γ_y) where { q = MeanField() }

    return x, mx_prev, vx_prev, x_prev, y, θ, γ
end


using BenchmarkTools

lar_model(::Type{ Multivariate }, order, c, stype) = lar_model_multivariate(order, c, stype, options = (limit_stack_depth = 50, ))
lar_model(::Type{ Univariate }, order, c, stype)   = lar_model_univariate(order, c, stype, options = (limit_stack_depth = 50, ))


# setup inference
function start_inference(data, order, niter, artype=Univariate, stype=ARsafe())
#     n = length(data)

    c = ReactiveMP.ar_unit(artype, order)


    x_t_min_prior = NormalMeanVariance(0.0, 1e7)
    γ_prior       = GammaShapeRate(0.001, 0.001)
    θ_prior       = MvNormalMeanPrecision(zeros(order), Matrix{Float64}(I, order, order))

    model, (x_t, mx_t_min, vx_t_min, x_t_min, y_t, θ, γ) = lar_model(artype, order, c, stype)

#     fe = Vector{Float64}()
    
    x_t_stream = Subject(Marginal)
    θ_stream = Subject(Marginal)
    γ_stream = Subject(Marginal)
    
    x_t_subscribtion = subscribe!(getmarginal(x_t, IncludeAll()), (x_t_posterior) -> next!(x_t_stream, x_t_posterior)
    )

    γ_subscription = subscribe!(getmarginal(γ, IncludeAll()), (γ_posterior) -> next!(γ_stream, γ_posterior)
    )
    
    θ_subscription = subscribe!(getmarginal(θ, IncludeAll()), (θ_posterior) -> next!(θ_stream, θ_posterior)
    )

    setmarginal!(x_t, x_t_min_prior)
    setmarginal!(γ, γ_prior)
    setmarginal!(θ, θ_prior)
#     γsub = subscribe!(getmarginal(γ), (mγ) -> γ_buffer = mγ)
#     θsub = subscribe!(getmarginal(θ), (mθ) -> θ_buffer = mθ)
#     xsub = subscribe!(getmarginals(x), (mx) -> copyto!(x_buffer, mx))
#     fesub = subscribe!(score(Float64, BetheFreeEnergy(), model), (f) -> push!(fe, f))

#     init_marginals(artype, order, γ, θ)

#     data_subscription = subscribe!(data, (d) -> update!(y_t, d))
    update!(y_t,data)
    for _ in 1:niter
        update!(mx_t_min, mean.(x_t_stream))
        update!(vx_t_min, var.(x_t_stream))
        update!(γ_shape, shape(γ_stream))
        update!(γ_rate, rate(γ_stream))
        update!(θ_shape, shape(θ_stream))
        update!(θ_rate, rate(θ_stream))
    end

#     return x_t_stream, γ_stream, () -> begin
#         unsubscribe!(x_t_subscribtion)
#         unsubscribe!(γ_subscription)
#         unsubscribe!(data_subscription)
#     end
end

function nextprice!(new_obs)

end