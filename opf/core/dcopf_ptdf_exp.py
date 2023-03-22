import pyomo.environ as pyo
from pyomo.core.util import quicksum
from pyomo.core.expr.numeric_expr import LinearExpression

def cnst_pf_ptdf_exp(m, e):
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg[g] for g in m.G])
    return m.pf[e] == m.load_injection[e] - m.gen_injection
    

def cnst_power_bal_ptdf_exp(m):
    return quicksum(m.pd[l] for l in m.L) == quicksum(m.pg[g] for g in m.G)
    