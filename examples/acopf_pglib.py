import opf
from pypglib import pglib_opf_case5_pjm

model = opf.build_model('acopf')
network = opf.parse_file(pglib_opf_case5_pjm)
model.instantiate(network)
result = model.solve(solver='ipopt',
                     solver_option={'print_level' : 4},
                     tee=True)
print(
    f"Status: {result['termination_status']}\n"
    f"Objective function: {result['obj_cost']}\n"
    f"Output power: {result['sol']['primal']['pg']}"
)

# To print computation time:
# print(f"Computation time: {result['time']}\n")

