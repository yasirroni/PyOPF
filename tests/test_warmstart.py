import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class WarmStartTest(unittest.TestCase):
    def test_warmstart_acopf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('acopf')
        self.assertEqual(model.model_type, 'acopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve(extract_dual = True)

        # instantiate new model
        model.instantiate(network)
        model.setup_warmstart(result['sol'])

        result_ws = model.solve(solver_option={
            'warm_start_init_point': 'yes',
            'warm_start_bound_push': 1e-12,
            'warm_start_mult_bound_push': 1e-12,
            'mu_init': 1e-10,
            'max_iter': 3,
        }, tee=True)

        self.assertEqual(result_ws['termination_status'], 'optimal')
        self.assertAlmostEqual(result['obj_cost'], 17551.89084, places=5)
        self.assertAlmostEqual(result_ws['obj_cost'], 17551.89084, places=5)


    def test_warmstart_dcopf_primal_only(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve()

        model.instantiate(network)
        model.setup_warmstart(result['sol'])

        # setup IPOPT options for warmstarting
        result_primal_only_ws = model.solve(solver_option={
            'warm_start_init_point': 'yes',
            'warm_start_bound_push': 1e-12,
            'warm_start_mult_bound_push': 1e-12,
            'mu_init': 1e-10,
            'max_iter': 3,
        }, tee=False)
        self.assertEqual(result_primal_only_ws['termination_status'], 'optimal')
        self.assertAlmostEqual(result['obj_cost'], 17479.89677, places=5)
        self.assertAlmostEqual(result_primal_only_ws['obj_cost'], 17479.89677, places=5)

    def test_warmstart_dcopf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)

        # extract dual solutions too
        model.instantiate(network)
        result = model.solve(extract_dual=True)
        
        model.instantiate(network)
        model.setup_warmstart(result['sol'])
        result_ws = model.solve(solver_option={
            'warm_start_init_point': 'yes',
            'warm_start_bound_push': 1e-12,
            'warm_start_mult_bound_push': 1e-12,
            'mu_init': 1e-10,
            'max_iter': 2,
        }, tee=False)
        
        self.assertEqual(result_ws['termination_status'], 'optimal')
        self.assertAlmostEqual(result_ws['obj_cost'], 17479.89677, places=5)


    def test_warmstart_dcopf_ptdf_primal_only(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf-ptdf')
        self.assertEqual(model.model_type, 'dcopf-ptdf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve()
        
        model.instantiate(network)
        model.setup_warmstart(result['sol']) # only primal

        # setup IPOPT options for warmstarting
        result_primal_only_ws = model.solve(solver_option={
            'warm_start_init_point': 'yes',
            'warm_start_bound_push': 1e-12,
            'warm_start_mult_bound_push': 1e-12,
            'mu_init': 1e-10,
            'max_iter': 10,
        }, tee=True)
        self.assertEqual(result_primal_only_ws['termination_status'], 'optimal')
        self.assertAlmostEqual(result['obj_cost'], 17479.89677, places=1)
        self.assertAlmostEqual(result_primal_only_ws['obj_cost'], 17479.89677, places=1)

    def test_warmstart_dcopf_ptdf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf-ptdf')
        self.assertEqual(model.model_type, 'dcopf-ptdf')
        network = opf.parse_file(matpower_fn)

        model.instantiate(network)
        result = model.solve(extract_dual = True)
        model.setup_warmstart(result['sol']) 
        
        result_ws = model.solve(solver_option={
            'warm_start_init_point': 'yes',
            'warm_start_bound_push': 1e-12,
            'warm_start_mult_bound_push': 1e-12,
            'mu_init': 1e-10,
            'max_iter': 2,
        }, tee=False)
        self.assertEqual(result_ws['termination_status'], 'optimal')
        self.assertAlmostEqual(result_ws['obj_cost'], 17479.89677, places=1)
