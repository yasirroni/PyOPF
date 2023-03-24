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
        solver = pyo.SolverFactory("ipopt")
        # solver.options['linear_solver'] = 'ma27'

        instance = model.instantiate(network)
        result = solver.solve(instance, tee=False) # solve first without warmstart

        warmstart_dict = {
            'primal': {}, 
            'dual': {},
            'bound': {}
        }
        # extract primal solutions
        primal_ws = warmstart_dict['primal']
        for v in instance.component_objects(pyo.Var, active=True):
            primal_ws_var = primal_ws.get(str(v), {})
            for idx in v:
                primal_ws_var[str(idx)] = v[idx].value
            primal_ws[str(v)] = primal_ws_var

        # extract dual solutions
        dual_ws = warmstart_dict['dual']
        for c in instance.component_objects(pyo.Constraint, active=True):
            dual_ws_cnst = dual_ws.get(str(c), {})
            for idx in c:
                dual_ws_cnst[str(idx)] = instance.dual[c[idx]]
            dual_ws[str(c)] = dual_ws_cnst

        # extract dual for bound constraint
        bound_ws = warmstart_dict['bound']
        for v in instance.component_objects(pyo.Var, active=True):
            bound_ws_var = bound_ws.get(str(v), {})
            for idx in v:
                if v[idx].lower is not None:
                    bound_ws_var["lb_"+str(idx)] = instance.ipopt_zL_out[v[idx]]
                if v[idx].upper is not None:
                    bound_ws_var["ub_"+str(idx)] = instance.ipopt_zU_out[v[idx]]
            bound_ws[str(v)] = bound_ws_var  
        print("bound_ws", bound_ws)
        # instantiate new model
        instance2 = model.instantiate(network)
        opf.setup_warmstart(instance2, warmstart_dict)

        # setup IPOPT options for warmstarting
        solver.options['warm_start_init_point'] = 'yes'
        solver.options['warm_start_bound_push'] = 1e-12
        solver.options['warm_start_mult_bound_push'] = 1e-12
        solver.options['mu_init'] = 1e-10
        solver.options['max_iter'] = 3

        result_ws = solver.solve(instance2, tee=False)
        
        self.assertEqual(result_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17551.89084, places=5)
        self.assertAlmostEqual(pyo.value(instance2.obj_cost), 17551.89084, places=5)

    def test_warmstart_dcopf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate(network)
        solver = pyo.SolverFactory("ipopt")
        # solver.options['linear_solver'] = 'ma27'
        result = solver.solve(instance, tee=False)

        warmstart_dict = {
            'primal': {}, 
            'dual': {},
            'bound': {}
        }
        # extract primal solutions
        primal_ws = warmstart_dict['primal']
        for v in instance.component_objects(pyo.Var, active=True):
            primal_ws_var = primal_ws.get(str(v), {})
            for idx in v:
                primal_ws_var[str(idx)] = v[idx].value
            primal_ws[str(v)] = primal_ws_var

        instance_primal_only_ws = model.instantiate(network)
        opf.setup_warmstart(instance_primal_only_ws, warmstart_dict)

        # setup IPOPT options for warmstarting
        solver.options['warm_start_init_point'] = 'yes'
        solver.options['warm_start_bound_push'] = 1e-12
        solver.options['warm_start_mult_bound_push'] = 1e-12
        solver.options['mu_init'] = 1e-10
        solver.options['max_iter'] = 10

        result_primal_only_ws = solver.solve(instance_primal_only_ws, tee=False)
        self.assertEqual(result_primal_only_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17479.89677, places=5)
        self.assertAlmostEqual(pyo.value(instance_primal_only_ws.obj_cost), 17479.89677, places=5)

        # extract dual solutions
        dual_ws = warmstart_dict['dual']
        for c in instance.component_objects(pyo.Constraint, active=True):
            dual_ws_cnst = dual_ws.get(str(c), {})
            for idx in c:
                dual_ws_cnst[str(idx)] = instance.dual[c[idx]]
            dual_ws[str(c)] = dual_ws_cnst

        # extract dual for bound constraint
        bound_ws = warmstart_dict['bound']
        for v in instance.component_objects(pyo.Var, active=True):
            bound_ws_var = bound_ws.get(str(v), {})
            for idx in v:
                if v[idx].lower is not None:
                    bound_ws_var["lb_"+str(idx)] = instance.ipopt_zL_out[v[idx]]
                if v[idx].upper is not None:
                    bound_ws_var["ub_"+str(idx)] = instance.ipopt_zU_out[v[idx]]
            bound_ws[str(v)] = bound_ws_var  

        # warmstart with both primal and dual solutions
        solver.options['max_iter'] = 2
        instance_ws = model.instantiate(network)
        opf.setup_warmstart(instance_ws, warmstart_dict)
        result_ws = solver.solve(instance_ws, tee=False)
        
        self.assertEqual(result_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance_ws.obj_cost), 17479.89677, places=5)

    def test_warmstart_dcopf_ptdf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf-ptdf')
        self.assertEqual(model.model_type, 'dcopf-ptdf')
        network = opf.parse_file(matpower_fn)
        instance = model.instantiate(network)
        solver = pyo.SolverFactory("ipopt")
        # solver.options['linear_solver'] = 'ma27'
        result = solver.solve(instance, tee=False)

        warmstart_dict = {
            'primal': {}, 
            'dual': {},
            'bound': {}
        }

        # extract primal solutions
        primal_ws = warmstart_dict['primal']
        for v in instance.component_objects(pyo.Var, active=True):
            primal_ws_var = primal_ws.get(str(v), {})
            for idx in v:
                primal_ws_var[str(idx)] = v[idx].value
            primal_ws[str(v)] = primal_ws_var

        instance_primal_only_ws = model.instantiate(network)
        opf.setup_warmstart(instance_primal_only_ws, warmstart_dict)

        # setup IPOPT options for warmstarting
        solver.options['warm_start_init_point'] = 'yes'
        solver.options['warm_start_bound_push'] = 1e-12
        solver.options['warm_start_mult_bound_push'] = 1e-12
        solver.options['mu_init'] = 1e-10
        solver.options['max_iter'] = 10

        result_primal_only_ws = solver.solve(instance_primal_only_ws, tee=False)
        self.assertEqual(result_primal_only_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance.obj_cost), 17479.89677, places=1)
        self.assertAlmostEqual(pyo.value(instance_primal_only_ws.obj_cost), 17479.89677, places=1)

        # extract dual solutions
        dual_ws = warmstart_dict['dual']
        for c in instance.component_objects(pyo.Constraint, active=True):
            dual_ws_cnst = dual_ws.get(str(c), {})
            for idx in c:
                dual_ws_cnst[str(idx)] = instance.dual[c[idx]]
            dual_ws[str(c)] = dual_ws_cnst

        # extract dual for bound constraint
        bound_ws = warmstart_dict['bound']
        for v in instance.component_objects(pyo.Var, active=True):
            bound_ws_var = bound_ws.get(str(v), {})
            for idx in v:
                if v[idx].lower is not None:
                    bound_ws_var["lb_"+str(idx)] = instance.ipopt_zL_out[v[idx]]
                if v[idx].upper is not None:
                    bound_ws_var["ub_"+str(idx)] = instance.ipopt_zU_out[v[idx]]
            bound_ws[str(v)] = bound_ws_var  

        # warmstart with both primal and dual solutions
        solver.options['max_iter'] = 2
        instance_ws = model.instantiate(network)
        opf.setup_warmstart(instance_ws, warmstart_dict)
        result_ws = solver.solve(instance_ws, tee=False)
        
        self.assertEqual(result_ws.solver.termination_condition.lower(), 'optimal')
        self.assertAlmostEqual(pyo.value(instance_ws.obj_cost), 17479.89677, places=1)
