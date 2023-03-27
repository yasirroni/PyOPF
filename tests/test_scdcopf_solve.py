import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class DCOPFSolveTest_case5(unittest.TestCase):
    def test_solve5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('scdcopf')
        self.assertEqual(model.model_type, 'scdcopf')
        

if __name__ == '__main__':
    unittest.main()