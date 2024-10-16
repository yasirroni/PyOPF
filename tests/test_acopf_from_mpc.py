import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo

class ACOPFSolveTestFromMPC(unittest.TestCase):
    def test_from_mpc(self):
        mpc = {
            'version': '2',
            'baseMVA': 100,
            'bus': [
                [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 230.0, 1.0, 1.1, 0.9],
                [2.0, 1.0, 300.0, 98.61, 0.0, 0.0, 1.0, 1.0, 0.0, 230.0, 1.0, 1.1, 0.9],
                [3.0, 2.0, 300.0, 98.61, 0.0, 0.0, 1.0, 1.0, 0.0, 230.0, 1.0, 1.1, 0.9],
                [4.0, 3.0, 400.0, 131.47, 0.0, 0.0, 1.0, 1.0, 0.0, 230.0, 1.0, 1.1, 0.9],
                [5.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 230.0, 1.0, 1.1, 0.9]
            ],
            'gen': [
                [1.0, 20.0, 0.0, 30.0, -30.0, 1.0, 100.0, 1.0, 40.0, 0.0],
                [1.0, 85.0, 0.0, 127.5, -127.5, 1.0, 100.0, 1.0, 170.0, 0.0],
                [3.0, 260.0, 0.0, 390.0, -390.0, 1.0, 100.0, 1.0, 520.0, 0.0],
                [4.0, 100.0, 0.0, 150.0, -150.0, 1.0, 100.0, 1.0, 200.0, 0.0],
                [5.0, 300.0, 0.0, 450.0, -450.0, 1.0, 100.0, 1.0, 600.0, 0.0]
            ],
            'gencost': [
                [2, 0, 0, 3, 0, 14, 0],
                [2, 0, 0, 3, 0, 15, 0],
                [2, 0, 0, 3, 0, 30, 0],
                [2, 0, 0, 3, 0, 40, 0],
                [2, 0, 0, 3, 0, 10, 0]
            ],
            'branch': [
                [1.0, 2.0, 0.00281, 0.0281, 0.00712, 400.0, 400.0, 400.0, 0.0, 0.0, 1.0, -30.0, 30.0],
                [1.0, 4.0, 0.00304, 0.0304, 0.00658, 426.0, 426.0, 426.0, 0.0, 0.0, 1.0, -30.0, 30.0],
                [1.0, 5.0, 0.00064, 0.0064, 0.03126, 426.0, 426.0, 426.0, 0.0, 0.0, 1.0, -30.0, 30.0],
                [2.0, 3.0, 0.00108, 0.0108, 0.01852, 426.0, 426.0, 426.0, 0.0, 0.0, 1.0, -30.0, 30.0],
                [3.0, 4.0, 0.00297, 0.0297, 0.00674, 426.0, 426.0, 426.0, 0.0, 0.0, 1.0, -30.0, 30.0],
                [4.0, 5.0, 0.00297, 0.0297, 0.00674, 240.0, 240.0, 240.0, 0.0, 0.0, 1.0, -30.0, 30.0]
            ]
        }

        model = opf.build_model('acopf')
        network = opf.io.mpc2pyopf(mpc)
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

if __name__ == '__main__':
    unittest.main()