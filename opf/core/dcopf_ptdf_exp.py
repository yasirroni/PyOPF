import pyomo.environ as pyo
from pyomo.core.util import quicksum


def cnst_pf_ptdf_exp(m, e):
    load_injection = [m.ptdf_l[e,l]*m.pd[l] for l in m.L]
    gen_injection = [m.ptdf_g[e,g]*m.pg[g] for g in m.G]
    return m.pf[e] == quicksum(load_injection) - quicksum(gen_injection) 
    

def cnst_power_bal_ptdf_exp(m):
    return quicksum(m.pd[l] for l in m.L) == quicksum(m.pg[g] for g in m.G)
    