using Revise
using Rocket
using ReactiveMP
using GraphPPL
using Distributions
using LinearAlgebra
import ProgressMeter
using PyCall
using HDF5
using BenchmarkTools


@model function lar_model_multivariate(order, c, stype)
    mx_prev = datavar(Vector{Float64})
    vx_prev = datavar(Matrix{Float64})
    γ_a = datavar(Float64)
    γ_b = datavar(Float64)
    m_θ = datavar(Vector{Float64})
    v_θ = datavar(Matrix{Float64})
    y = datavar(Float64)

    θ  ~ MvNormalMeanCovariance(m_θ, v_θ) where { q = MeanField() }
    x_prev ~ MvNormalMeanCovariance(mx_prev, vx_prev) where { q = MeanField() }

    γ  ~ GammaShapeRate(γ_a, γ_b) where { q = MeanField() }

    γ_y = constvar(1.0)
    ct  = constvar(c)

    meta = ARMeta(Multivariate, order, stype)

    ar_node, x_out ~ AR(x_prev, θ, γ) where { q = q(y, x)q(γ)q(θ), meta = meta }
    y ~ NormalMeanPrecision(dot(ct, x_out), γ_y) where { q = MeanField() }

    return x_out, mx_prev, vx_prev, x_prev, y, θ,m_θ,v_θ, γ, γ_a,γ_b,ar_node
end



lar_model(::Type{ Multivariate }, order, c, stype) = lar_model_multivariate(order, c, stype, options = (limit_stack_depth = 50, ))
lar_model(::Type{ Univariate }, order, c, stype)   = lar_model_univariate(order, c, stype, options = (limit_stack_depth = 50, ))


# setup inference
function inference(data,mx_min,vx_min,mθ,vθ,γa,γb, order, niter, artype=Multivariate, stype=ARsafe())

    c = ReactiveMP.ar_unit(artype, order)

    model, (x_t, mx_t_min, vx_t_min, x_t_min, y_t, θ, m_θ,v_θ,γ,γ_a,γ_b,ar_node) = lar_model(artype, order, c, stype)

    x_t_current = MvNormalMeanCovariance(zeros(order),diageye(order))
    θ_current = MvNormalMeanCovariance(mθ, vθ)  # use posteriors of previous evaluation
    γ_current = GammaShapeRate(γa, γb)  # use previous

    x_t_stream = keep(Marginal)
    θ_stream = keep(Marginal)
    γ_stream = keep(Marginal)

    x_t_subscribtion = subscribe!(getmarginal(x_t), (x_t_posterior) -> next!(x_t_stream, x_t_posterior))
    γ_subscription = subscribe!(getmarginal(γ), (γ_posterior) -> next!(γ_stream, γ_posterior))
    θ_subscription = subscribe!(getmarginal(θ), (θ_posterior) -> next!(θ_stream, θ_posterior))

    setmarginal!(x_t, x_t_current)
    setmarginal!(γ, γ_current)
    setmarginal!(θ, θ_current)
    setmarginal!(ar_node, :y_x, MvNormalMeanPrecision(zeros(2*order), Matrix{Float64}(I, 2*order, 2*order)))

    # update with the variable values, not with the initial distribution values
    for _ in 1:niter
        update!(y_t, data)
        update!(mx_t_min, mx_min)
        update!(vx_t_min, vx_min)
        update!(γ_a, γa)
        update!(γ_b, γb)
        update!(m_θ, mθ)
        update!(v_θ, vθ)
    end

return mean(x_t_stream[end]), cov(x_t_stream[end]), mean(θ_stream[end]), cov(θ_stream[end]), shape(γ_stream[end]), rate(γ_stream[end])
end

