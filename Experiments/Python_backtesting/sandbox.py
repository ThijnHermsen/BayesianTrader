import julia
jl = julia.Julia()
# jl = julia.Julia(compiled_modules=False)
from julia import Main
Main.include('jl_experiment.jl')

# jl_ret1 = Main.test_fun("hoi")
# jl_ret2 = Main.test_fun2("hoi")
# jl_ret3 = Main.test_fun3(3, 8)
# jl_ret4 = Main.test_fun4(3, 8)
#
# print(jl_ret1)
# print(jl_ret2)
# print(jl_ret3)
# print(jl_ret4)





# from julia.api import LibJulia, JuliaInfo
# jl_exe_path = r"C:\Users\s154857\AppData\Local\Programs\Julia-1.6.1\bin\julia.exe"
# api = LibJulia.load(julia=jl_exe_path)
# api.init_julia()
# from julia.api import JuliaInfo
# info = JuliaInfo.load(julia=jl_exe_path)
# print(info.julia)
# print(info.sysimage)
# print(info.python)
# print(info.is_compatible_python())

# import julia
# jl = julia.Julia()
# test_fun = jl.evalfile("jl_experiment.jl")
#
# jl_ret = test_fun("hoi")
#

# from julia import Julia
# jl = Julia()
# jl.include("jl_experiment.jl")
# jl_ret = jl.test_fun2("hoi")

# test_fun = jl.evalfile("jl_experiment.jl")
#
# jl_ret = test_fun("hoi")

