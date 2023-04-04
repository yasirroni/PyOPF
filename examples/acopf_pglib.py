import opf
from pypglib import pglib_opf_case5_pjm

model = opf.build_model('acopf')
network = opf.parse_file(pglib_opf_case5_pjm)
model.instantiate(network)
result = model.solve(solver='ipopt',
                     solver_option={'print_level' : 5, 'linear_solver': 'ma27'},
                     tee=True)
