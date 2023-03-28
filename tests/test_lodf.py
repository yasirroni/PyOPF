import unittest
import opf
from pathlib import Path
import pyomo.environ as pyo
import numpy as np


class LODFTest(unittest.TestCase):
    def test_ptdf_case5(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        network = opf.parse_file(matpower_fn)
        outage_branchidxs = [0,1,2]
        lodf = opf.compute_lodf(network,outage_branchidxs)
        lodf_gt = [[-1.         ,  0.34479465,  0.30707071],
                   [ 0.54285714 , -1.,          0.69292929],
                   [ 0.45714286 ,  0.65520535, -1.        ],
                   [-1.         ,  0.34479465,  0.30707071],
                   [-1.         ,  0.34479465,  0.30707071],
                   [-0.45714286 , -0.65520535,  1.        ]]
        np.testing.assert_almost_equal(lodf, lodf_gt)
        

    def test_ptdf_case5_solve(self):
        matpower_fn = Path("./data/pglib_opf_case5_pjm.m")
        model = opf.build_model('dcopf')

        network = opf.parse_file(matpower_fn)
        outage_branchidxs = [2,0]
        lodf = opf.compute_lodf(network,outage_branchidxs)

        model.instantiate(network)
        result = model.solve(tee=False)
        pf = result['sol']['primal']['pf']
        pg = result['sol']['primal']['pg']
        pf_vec = np.asarray([pfval for pfid, pfval in pf.items()])
        pg_vec = np.asarray([pgval for pgid, pgval in pg.items()])
        pd_vec = np.asarray([model.instance.pd[pdid].value for pdid in model.instance.pd])
        pf_ke = pf_vec + lodf[:,0] * pf_vec[outage_branchidxs[0]]
        I_g = opf.compute_generator_incidence_matrix(network)
        I_l = opf.compute_load_incidence_matrix(network)
        I_e = opf.compute_line_incidence_matrix(network)
        p_bal = I_e @ pf_vec - I_g @ pg_vec + I_l @ pd_vec
        p_bal_ke = I_e @ pf_ke - I_g @ pg_vec + I_l @ pd_vec
        np.testing.assert_almost_equal(p_bal, np.zeros_like(p_bal))
        np.testing.assert_almost_equal(p_bal_ke, np.zeros_like(p_bal_ke))

    def test_ptdf_case14_solve(self):
        matpower_fn = Path("./data/pglib_opf_case14_ieee.m")
        model = opf.build_model('dcopf')

        network = opf.parse_file(matpower_fn)
        outage_branchidxs = [0]
        lodf = opf.compute_lodf(network,outage_branchidxs)

        model.instantiate(network)
        result = model.solve(tee=False)
        pf = result['sol']['primal']['pf']
        pg = result['sol']['primal']['pg']
        pf_vec = np.empty(len(pf))
        pg_vec = np.empty(len(pg))
        pd_vec = np.empty(len(network['load']))
        for genid, gen in network['gen'].items():
            pg_vec[gen['index']] = pg[genid]
        for branchid, branch in network['branch'].items():
            pf_vec[branch['index']] = pf[branchid]
        for loadid, load in network['load'].items():
            pd_vec[load['index']] = model.instance.pd[loadid].value
            
        pf_ke = pf_vec + lodf[:,0] * pf_vec[outage_branchidxs[0]]
        I_g = opf.compute_generator_incidence_matrix(network)
        I_l = opf.compute_load_incidence_matrix(network)
        I_e = opf.compute_line_incidence_matrix(network)
        p_bal = I_e @ pf_vec - I_g @ pg_vec + I_l @ pd_vec
        p_bal_ke = I_e @ pf_ke - I_g @ pg_vec + I_l @ pd_vec
        np.testing.assert_almost_equal(p_bal, np.zeros_like(p_bal))
        np.testing.assert_almost_equal(p_bal_ke, np.zeros_like(p_bal_ke))