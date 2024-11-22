import pyomo.environ as pyo
from pyomo.core.util import quicksum

def bound_pg_exp(m, g):
    return (0, m.pgmax[g])

def cnst_gav_exp(m, g):
    return m.uc[g] - m.gav[g] <= 0.

def const_pg_max_uc_exp(m, g):
    return (
        m.pg[g] - m.pgmax[g] * m.uc[g] <= 0.
    )

def const_pg_min_uc_exp(m, g):
    return (
        m.pg[g] - m.pgmin[g] * m.uc[g] >= 0.
    )

def const_qg_max_uc_exp(m, g):
    return (
        m.qg[g] - m.qgmax[g] * m.uc[g] <= 0.
    )

def const_qg_min_uc_exp(m, g):
    return (
        m.qg[g] - m.qgmin[g] * m.uc[g] >= 0.
    )
