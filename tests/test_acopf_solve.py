import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class ACOPFSolveTest(unittest.TestCase):
    def test_parse(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('acopf')
        self.assertEqual(model.model_type, 'acopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve('ipopt', tee=True)

        self.assertEqual(result['termination_status'], 'optimal')
        
        self.assertAlmostEqual(result['obj_cost'], 17551.8908385928)
        self.assertAlmostEqual(result['sol']['primal']['pg']['1'], 0.4000000096583169)
        self.assertAlmostEqual(result['sol']['primal']['pg']['2'], 1.700000016481886)
        self.assertAlmostEqual(result['sol']['primal']['pg']['3'], 3.244984943109816)
        self.assertAlmostEqual(result['sol']['primal']['pg']['4'], -6.499551061768208e-09)
        self.assertAlmostEqual(result['sol']['primal']['pg']['5'], 4.706935997017106)

        self.assertAlmostEqual(result['sol']['primal']['qg']['1'], 0.30000000718720293)
        self.assertAlmostEqual(result['sol']['primal']['qg']['2'], 1.2750000099425889)
        self.assertAlmostEqual(result['sol']['primal']['qg']['3'], 3.90000002936748)
        self.assertAlmostEqual(result['sol']['primal']['qg']['4'], -0.10802298184685119)
        self.assertAlmostEqual(result['sol']['primal']['qg']['5'], -1.6503940883937465)

        self.assertAlmostEqual(result['sol']['primal']['vm']['1'], 1.0776176598114897)

        self.assertAlmostEqual(result['sol']['primal']['va']['1'], 0.048935231558520996)

class ACOPFSolveVariantTest(unittest.TestCase):
    def test_parse(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('acopf')
        self.assertEqual(model.is_constructed(),False)
        self.assertEqual(model.model_type, 'acopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)

        # after instantiating, we can change some parameter values
        model.instance.pd['1'] = 1. # it was originally 3.

        # then solve
        result = model.solve('ipopt', tee=True)
        
        self.assertAlmostEqual(result['obj_cost'], 12250.188059667513) # cost is decreased to meet lower demand
        self.assertAlmostEqual(result['sol']['primal']['pg']['1'], 0.4000000096567134)
        self.assertAlmostEqual(result['sol']['primal']['pg']['2'], 1.7000000164781899)
        self.assertAlmostEqual(result['sol']['primal']['pg']['3'], 1.5960349869167256)
        self.assertAlmostEqual(result['sol']['primal']['pg']['4'], -6.798649788930885e-09)
        self.assertAlmostEqual(result['sol']['primal']['pg']['5'], 4.352083087875251)


        self.assertAlmostEqual(result['sol']['primal']['vm']['1'], 1.0779474018698787)
        self.assertAlmostEqual(result['sol']['primal']['vm']['2'], 1.0857370279890064)
        self.assertAlmostEqual(result['sol']['primal']['vm']['3'], 1.100000010096072)
        self.assertAlmostEqual(result['sol']['primal']['vm']['4'], 1.0641852468403687)
        self.assertAlmostEqual(result['sol']['primal']['vm']['5'], 1.0690083133156378)

if __name__ == '__main__':
    unittest.main()