
using Revise
using Rocket
using ReactiveMP
using GraphPPL
using Distributions
using LinearAlgebra
import ProgressMeter
using PyCall
using HDF5


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

    ar_node, x ~ AR(x_prev, θ, γ) where { q = q(y, x_prev)q(γ)q(θ), meta = meta }
    y ~ NormalMeanPrecision(dot(ct, x), γ_y) where { q = MeanField() }

    return x, mx_prev, vx_prev, x_prev, y, θ,m_θ,v_θ, γ, γ_a,γ_b,ar_node
end


using BenchmarkTools

lar_model(::Type{ Multivariate }, order, c, stype) = lar_model_multivariate(order, c, stype, options = (limit_stack_depth = 50, ))
lar_model(::Type{ Univariate }, order, c, stype)   = lar_model_univariate(order, c, stype, options = (limit_stack_depth = 50, ))

mutable struct BookKeeper
    mx_min :: Vector{Float64}
    vx_min :: Matrix{Float64}
    mθ :: Vector{Float64}
    vθ :: Matrix{Float64}
    γa :: Float64
    γb :: Float64
end

function update_BookKeeper!(bk::BookKeeper,mx_min,vx_min,mθ,vθ,γa,γb)
    bk.mx_min = mx_min
    bk.vx_min = vx_min
    bk.mθ = mθ
    bk.vθ = vθ
    bk.γa = γa
    bk.γb = γb
end

# setup inference
function start_inference(data,mx_min,vx_min,mθ,vθ,γa,γb, order, niter, artype=Multivariate, stype=ARsafe())


#     mx_min = BookKeeper.mx_min
#     vx_min = BookKeeper.vx_min
#     mθ = BookKeeper.mθ
#     vθ = BookKeeper.vθ
#     γa = BookKeeper.γa
#     γb = BookKeeper.γb
#     println(mx_min)
#     println(PyArray(mx_min))
#     myfile = h5open("./vars/ar_order.hdf5", "r")
#     mx_min = read(myfile, "mx_min")
#     vx_min = read(myfile, "vx_min")
#     mθ = read(myfile, "mtheta")
#     vθ = read(myfile, "vtheta")
#     γa = read(myfile, "gamma_a")
#     γb = read(myfile, "gamma_b")
#     close(myfile)

    c = ReactiveMP.ar_unit(artype, order)

    model, (x_t, mx_t_min, vx_t_min, x_t_min, y_t, θ, m_θ,v_θ,γ,γ_a,γ_b,ar_node) = lar_model(artype, order, c, stype)
    
    x_t_current = MvNormalMeanCovariance(zeros(order),diageye(order))
    θ_current = MvNormalMeanCovariance(zeros(order),diageye(order))
    γ_current = vague(Gamma)
    
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
   
    
    update!(mx_t_min, mx_min)
    update!(vx_t_min, vx_min)
    update!(γ_a, γa)
    update!(γ_b, γb)
    update!(m_θ, mθ)
    update!(v_θ, vθ)
    
    for _ in 1:niter
        update!(y_t, data)
        update!(mx_t_min, mean(x_t_current))
        update!(vx_t_min, cov(x_t_current))
        update!(γ_a, shape(γ_current))
        update!(γ_b, rate(γ_current))
        update!(m_θ, mean(θ_current))
        update!(v_θ, cov(θ_current))
    end

#     x_t_stream ,θ_stream ,γ_stream

return mean(x_t_stream[end]), cov(x_t_stream[end]), mean(θ_stream[end]), cov(θ_stream[end]), shape(γ_stream[end]), rate(γ_stream[end])
end

# xs,θs, γs = start_inference(2.0,zeros(4), diageye(4), zeros(4),diageye(4),0.1,0.1,4,20);