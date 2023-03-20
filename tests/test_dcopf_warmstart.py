import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class DCOPFWarmStartTest(unittest.TestCase):
    def test_warmstart_dcopf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate_model(network)
        solver = pyo.SolverFactory("ipopt")
        result = solver.solve(instance, tee=False)

        warmstart_dict = {
            'primal': {}, 
            'dual': {}
        }
        # extract primal solutions
        primal_ws = warmstart_dict['primal']
        for v in instance.component_objects(pyo.Var, active=True):
            primal_ws_var = primal_ws.get(str(v), {})
            for idx in v:
                primal_ws_var[idx] = v[idx].value
            primal_ws[str(v)] = primal_ws_var

        instance_primal_only_ws = model.instantiate_model(network)
        opf.setup_warmstart(instance_primal_only_ws, warmstart_dict)

        # setup IPOPT options for warmstarting
        solver.options['warm_start_init_point'] = 'yes'
        solver.options['warm_start_bound_push'] = 1e-12
        solver.options['warm_start_mult_bound_push'] = 1e-12
        solver.options['mu_init'] = 1e-10
        solver.options['max_iter'] = 10

        result_primal_only_ws = solver.solve(instance_primal_only_ws, tee=True)
        self.assertEqual(result_primal_only_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17479.89677, places=5)
        self.assertAlmostEqual(pyo.value(instance_primal_only_ws.obj_cost), 17479.89677, places=5)

        # extract dual solutions
        dual_ws = warmstart_dict['dual']
        for c in instance.component_objects(pyo.Constraint, active=True):
            dual_ws_cnst = dual_ws.get(str(c), {})
            for idx in c:
                dual_ws_cnst[idx] = instance.dual[c[idx]]
            dual_ws[str(c)] = dual_ws_cnst

        solver.options['max_iter'] = 2
        result_ws = solver.solve(instance_primal_only_ws, tee=True)
        
        self.assertEqual(result_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance_primal_only_ws.obj_cost), 17479.89677, places=5)


