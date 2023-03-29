import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class SCDCOPFSolveTest_case5(unittest.TestCase):
    def test_solve5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        network = opf.parse_file(matpower_fn)
        
        # solve naive DCOPF model
        model_dcopf = opf.build_model('dcopf')
        model_dcopf.instantiate(network)
        result_dcopf = model_dcopf.solve()

        # solve SC-DCOPF without any contingencies
        model = opf.build_model('scdcopf')
        model.instantiate(network, generator_contingency=[], line_contingency=[])
        result_scdcopf_wo_contingency = model.solve('ipopt')
        self.assertAlmostEqual(result_dcopf['obj_cost'], result_scdcopf_wo_contingency['obj_cost'], places=1)

        # tweak the input network value so that when contingencies occur, it still has some feasible region
        network['load']['1']['pd'] = 1.25
        network['load']['2']['pd'] = 1.25
        network['load']['3']['pd'] = 1.25
        network['gen']['2']['pmax'] = 7.
        network['gen']['3']['pmax'] = 7.

        model.instantiate(network, generator_contingency='all', line_contingency='all', gamma=0.05, eps=1e-4) # consider all contingencies
        # result_gurobi = model.solve('gurobi', solver_option={'NonConvex': 2}, tee=True, extract_contingency=True)
        result_ipopt = model.solve('ipopt', tee=False, extract_contingency=True)
        
        self.assertAlmostEqual(result_ipopt['obj_cost'], 8857., places=1)
        
    def test_solve14(self):
        matpower_fn = Path("./data/pglib_opf_case14_ieee.m")
        network = opf.parse_file(matpower_fn)
        
        # solve naive DCOPF model
        model_dcopf = opf.build_model('dcopf')
        model_dcopf.instantiate(network)
        result_dcopf = model_dcopf.solve()

        # solve SC-DCOPF without any contingencies
        model = opf.build_model('scdcopf')
        model.instantiate(network, generator_contingency=[], line_contingency=[])
        result_scdcopf_wo_contingency = model.solve('ipopt')
        self.assertAlmostEqual(result_dcopf['obj_cost'], result_scdcopf_wo_contingency['obj_cost'], places=1)

        # tweak the input network value so that when contingencies occur, it still has some feasible region
        for loadid, load in network['load'].items():
            load['pd'] = 0.1 * load['pd']

        model.instantiate(network, generator_contingency='all', line_contingency='all', gamma=0.1, eps=1e-8) # consider all contingencies
        # result_gurobi = model.solve('gurobi', solver_option={'NonConvex': 2}, tee=True, extract_contingency=True)
        result_ipopt = model.solve('ipopt', tee=False, extract_contingency=True)
        # print(result_gurobi['obj_cost'])
        print(result_ipopt['obj_cost'])
        self.assertAlmostEqual(result_ipopt['obj_cost'], 512.1235, places=3)


if __name__ == '__main__':
    unittest.main()