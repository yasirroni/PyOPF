import pyomo.environ as pyo
from pyomo.core.util import quicksum
from pyomo.core.expr.numeric_expr import LinearExpression

def pg_kg_bound_exp(m, g, k):
    if g == k:
        return (0.,0.)
    else:
        return (m.pgmin[g], m.pgmax[g])

def cnst_pf_repr_exp(m, e):
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg[g] for g in m.G])
    return m.pf[e] == m.gen_injection - m.load_injection[e]

def cnst_pf_kg_exp(m, e, k):
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg_kg[g,k] for g in m.G])
    return (-m.rate_c[e], m.gen_injection - m.load_injection[e], m.rate_c[e])

def cnst_pf_ke_exp(m, e, k):
    return (-m.rate_c[e], m.pf[e] + m.lodf[e,k]*m.pf[k], m.rate_c[e])


""" Relaxation of the complementarity constraint to represent linear primary response
    Ref: Petra, Cosmin G., and Ignacio Aravena. 
         "Solving realistic security-constrained optimal power flow problems." 
         arXiv preprint arXiv:2110.01669 (2021).
"""
def cnst_pr_kg1_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.pg_kg[g,k] + m.rho_kg[g,k] == m.pg[g] + m.n_kg[k]*m.gamma[g]*m.pgcapa[g]

def cnst_pr_kg2_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.rho_kg[g,k] * (m.pgmax[g]-m.pg_kg[g,k]) <= m.eps * m.pgcapa[g]

def cnst_power_bal_ptdf_kg_exp(m, k):
    return quicksum(m.pd[l] for l in m.L) == quicksum(m.pg_kg[g,k] for g in m.G)


# ================================================================================
# Only for SC-DC-OPF-CCGA 
# ================================================================================
def cnst_pf_kg_lazy_exp(m, e_k):
    e,k = e_k
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg_kg[g,k] for g in m.G])
    return (-m.rate_c[e], m.gen_injection - m.load_injection[e], m.rate_c[e])

def cnst_pf_ke_lazy_exp(m, e_k):
    e,k = e_k
    return (-m.rate_c[e], m.pf[e] + m.lodf[e,k]*m.pf[k], m.rate_c[e])

def cnst_provisional_kg_exp(m, g, k): # Eq. (36) in the SCDCOPF-CCGA paper # to ensure solution is obtainable through binary search
    return m.pg_kg[g,k] - m.pg[g] <= m.r_bar[g]
