import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class DCOPFSolveTest_case5(unittest.TestCase):
    def test_solve5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve()
        
        self.assertEqual(result['termination_status'], 'optimal')
        
        self.assertAlmostEqual(result['obj_cost'], 17479.896769813888)
            
        self.assertAlmostEqual(result['sol']['primal']['pg']['1'], 0.4000000096631537)
        self.assertAlmostEqual(result['sol']['primal']['pg']['2'], 1.7000000164929279)
        self.assertAlmostEqual(result['sol']['primal']['pg']['3'], 3.2349483673666066)
        self.assertAlmostEqual(result['sol']['primal']['pg']['4'], 7.656316434159741e-09)
        self.assertAlmostEqual(result['sol']['primal']['pg']['5'], 4.6650515988209955)

        self.assertAlmostEqual(result['sol']['primal']['va']['1'], -0.05735150733969868)
        self.assertAlmostEqual(result['sol']['primal']['va']['2'], 0.01352060911369567)
        self.assertAlmostEqual(result['sol']['primal']['va']['3'], 0.008035714369804532)
        self.assertAlmostEqual(result['sol']['primal']['va']['4'], 0.0)
        self.assertAlmostEqual(result['sol']['primal']['va']['5'], -0.07199280071944555)


class DCOPFSolveTest_case14(unittest.TestCase):
    def test_solve14(self):
        matpower_fn = Path("./data/pglib_opf_case14_ieee.m")
        model = opf.build_model('dcopf')
        self.assertEqual(model.model_type, 'dcopf')
        network = opf.parse_file(matpower_fn)
        model.instantiate(network)
        result = model.solve()

        self.assertEqual(result['termination_status'], 'optimal')
        
        self.assertAlmostEqual(result['obj_cost'], 2051.5262699779273, places=4)
        self.assertAlmostEqual(result['sol']['primal']['pg']['1'], 2.5899999800011604)
        self.assertAlmostEqual(result['sol']['primal']['pg']['2'], -9.962008701445461e-09)
        self.assertAlmostEqual(result['sol']['primal']['va']['1'], 0.0)
        self.assertAlmostEqual(result['sol']['primal']['va']['2'], 0.11768346281509813)
        self.assertAlmostEqual(result['sol']['primal']['pf']['1'], 1.7962128752942261)
        self.assertAlmostEqual(result['sol']['primal']['pf']['2'], 0.7937871047069344)

        

if __name__ == '__main__':
    unittest.main()