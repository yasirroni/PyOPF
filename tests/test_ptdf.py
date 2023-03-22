import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo
import numpy as np


class PTDFTest(unittest.TestCase):
    def test_ptdf(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        network = opf.parse_file(matpower_fn)
        ptdf_g, ptdf_l = opf.compute_ptdf(network)
        
        self.assertEqual(ptdf_g.shape, (6,5))
        self.assertEqual(ptdf_l.shape, (6,3))
        ptdf_g_true = np.asarray(
         [[ 0.19391661,  0.19391661, -0.34898946,  0.,   0.15953804],
          [ 0.43758813,  0.43758813,  0.18945142,  0.,   0.36001018],
          [ 0.36849527,  0.36849527,  0.15953804,  0.,  -0.51954822],
          [ 0.19391661,  0.19391661, -0.34898946,  0.,   0.15953804],
          [ 0.19391661,  0.19391661,  0.65101054,  0.,   0.15953804],
          [-0.36849527, -0.36849527, -0.15953804,  0.,  -0.48045178]]
        )
        np.testing.assert_almost_equal(ptdf_g, ptdf_g_true)

        ptdf_l_true = np.asarray(
            [[-0.47589472, -0.34898946,  0. ],
             [ 0.25834285,  0.18945142,  0. ],
             [ 0.21755187,  0.15953804,  0. ],
             [ 0.52410528, -0.34898946,  0. ],
             [ 0.52410528,  0.65101054,  0. ],
             [-0.21755187, -0.15953804,  0. ]]
        )
        np.testing.assert_almost_equal(ptdf_l, ptdf_l_true)