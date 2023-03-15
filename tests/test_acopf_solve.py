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
        instance = model.instantiate_model(network)
        solver = pyo.SolverFactory("ipopt")
        results = solver.solve(instance, tee=False)

        self.assertEqual(results.solver.termination_condition, 'optimal')
        
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17551.8908385928)
        self.assertAlmostEqual(pyo.value(instance.pg[1]), 0.4000000096583169)
        self.assertAlmostEqual(pyo.value(instance.pg[2]), 1.700000016481886)
        self.assertAlmostEqual(pyo.value(instance.pg[3]), 3.244984943109816)
        self.assertAlmostEqual(pyo.value(instance.pg[4]), -6.499551061768208e-09)
        self.assertAlmostEqual(pyo.value(instance.pg[5]), 4.706935997017106)

        self.assertAlmostEqual(pyo.value(instance.qg[1]), 0.30000000718720293)
        self.assertAlmostEqual(pyo.value(instance.qg[2]), 1.2750000099425889)
        self.assertAlmostEqual(pyo.value(instance.qg[3]), 3.90000002936748)
        self.assertAlmostEqual(pyo.value(instance.qg[4]), -0.10802298184685119)
        self.assertAlmostEqual(pyo.value(instance.qg[5]), -1.6503940883937465)

        self.assertAlmostEqual(pyo.value(instance.vm[1]), 1.0776176598114897)
        self.assertAlmostEqual(pyo.value(instance.vm[2]), 1.0840647498863991)
        self.assertAlmostEqual(pyo.value(instance.vm[3]), 1.1000000103814849)
        self.assertAlmostEqual(pyo.value(instance.vm[4]), 1.0641372651432481)
        self.assertAlmostEqual(pyo.value(instance.vm[5]), 1.0690706714261342)

        self.assertAlmostEqual(pyo.value(instance.va[1]), 0.048935231558520996)
        self.assertAlmostEqual(pyo.value(instance.va[2]), -0.01282196125100345)
        self.assertAlmostEqual(pyo.value(instance.va[3]), -0.009769052947235861)
        self.assertAlmostEqual(pyo.value(instance.va[4]), 8.666684749742561e-34)
        self.assertAlmostEqual(pyo.value(instance.va[5]), 0.0626633886769194)

class ACOPFSolveVariantTest(unittest.TestCase):
    def test_parse(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('acopf')
        self.assertEqual(model.model_type, 'acopf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate_model(network)

        # after instantiating, we can change some parameter values
        instance.pd[1] = 1. # it was originally 3.

        # then solve
        solver = pyo.SolverFactory("ipopt")
        results = solver.solve(instance, tee=False)
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 12250.188059667513) # cost is decreased to meet lower demand
        self.assertAlmostEqual(pyo.value(instance.pg[1]), 0.4000000096567134)
        self.assertAlmostEqual(pyo.value(instance.pg[2]), 1.7000000164781899)
        self.assertAlmostEqual(pyo.value(instance.pg[3]), 1.5960349869167256)
        self.assertAlmostEqual(pyo.value(instance.pg[4]), -6.798649788930885e-09)
        self.assertAlmostEqual(pyo.value(instance.pg[5]), 4.352083087875251)

        self.assertAlmostEqual(pyo.value(instance.qg[1]), 0.3000000071152888)
        self.assertAlmostEqual(pyo.value(instance.qg[2]), 1.2750000098709706)
        self.assertAlmostEqual(pyo.value(instance.qg[3]), 3.900000033589449)
        self.assertAlmostEqual(pyo.value(instance.qg[4]), -0.10775023757250281)
        self.assertAlmostEqual(pyo.value(instance.qg[5]), -1.688756480064634)

        self.assertAlmostEqual(pyo.value(instance.vm[1]), 1.0779474018698787)
        self.assertAlmostEqual(pyo.value(instance.vm[2]), 1.0857370279890064)
        self.assertAlmostEqual(pyo.value(instance.vm[3]), 1.100000010096072)
        self.assertAlmostEqual(pyo.value(instance.vm[4]), 1.0641852468403687)
        self.assertAlmostEqual(pyo.value(instance.vm[5]), 1.0690083133156378)

        self.assertAlmostEqual(pyo.value(instance.va[1]), 0.050902054558099055)
        self.assertAlmostEqual(pyo.value(instance.va[2]), -0.0004917772997671698)
        self.assertAlmostEqual(pyo.value(instance.va[3]), -0.01167545818917585)
        self.assertAlmostEqual(pyo.value(instance.va[4]), -6.29688813848483e-34)
        self.assertAlmostEqual(pyo.value(instance.va[5]), 0.0626748680527582)

if __name__ == '__main__':
    unittest.main()