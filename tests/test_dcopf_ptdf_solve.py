import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class DCOPFPTDFSolveTest(unittest.TestCase):
    def test_solve_case5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf-ptdf')
        self.assertEqual(model.model_type, 'dcopf-ptdf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate_model(network)
        solver = pyo.SolverFactory("ipopt")
        results = solver.solve(instance, tee=False)

        self.assertEqual(results.solver.termination_condition, 'optimal')
        
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17479.896769813888, places=3)
            
        self.assertAlmostEqual(pyo.value(instance.pg[1]), 0.4000000096631537)
        self.assertAlmostEqual(pyo.value(instance.pg[2]), 1.7000000164929279)
        self.assertAlmostEqual(pyo.value(instance.pg[3]), 3.2349483673666066)
        self.assertAlmostEqual(pyo.value(instance.pg[4]), 7.656316434159741e-09)
        self.assertAlmostEqual(pyo.value(instance.pg[5]), 4.6650515988209955)


    def test_solve_case14(self):
        matpower_fn = Path("./data/pglib_opf_case14_ieee.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate_model(network)
        solver = pyo.SolverFactory("ipopt")
        solver.options['linear_solver'] = 'ma27'
        results = solver.solve(instance, tee=False)

        self.assertEqual(results.solver.termination_condition, 'optimal')
        
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 2051.5262699779273, places=4)
        self.assertAlmostEqual(pyo.value(instance.pg[1]), 2.5899999800011604)
        self.assertAlmostEqual(pyo.value(instance.pg[2]), -9.962008701445461e-09)

