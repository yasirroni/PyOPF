import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class SCDCOPF_CCGA_SolveTest_case5(unittest.TestCase):
    def test_solve5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        network = opf.parse_file(matpower_fn)
        network['gen']['2']['pmax'] = 7.

        model = opf.build_model('scdcopf-ccga')
        model.instantiate(network, generator_contingency='all', line_contingency=[], verbose=False, gamma=0.2, eps=1e-5)
        result = model.solve('ipopt', tee=True)
        print(result)

        