import pyomo.environ as pyo
from pyomo.core.util import quicksum
from pyomo.core.expr.numeric_expr import LinearExpression

def pg_kg_bound_exp(m, g, k):
    return (m.pgmin[g], m.pgmax[g])

def pg_ke_bound_exp(m, g, k):
    return (m.pgmin[g], m.pgmax[g])

def cnst_pf_repr_exp(m, e):
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg[g] for g in m.G])
    return m.pf[e] == m.load_injection[e] - m.gen_injection

def cnst_pf_kg_exp(m, e, k):
    m.gen_injection = LinearExpression(constant=0, linear_coefs=m.ptdf_g[e], linear_vars=[m.pg_kg[g,k] for g in m.G])
    return (-m.rate_a[e], m.load_injection[e] - m.gen_injection, m.rate_a[e])

def cnst_pf_ke_exp(m, e, k):
    return (-m.rate_a[e], m.pf[e] + m.lodf[e,k]*m.pf[k], m.rate_a[e])

def cnst_pg_kg_exp(m, k):
    return m.pg_kg[k,k] == 0.



""" Relaxation of the complementarity constraint to represent linear primary response
    Ref: Petra, Cosmin G., and Ignacio Aravena. 
         "Solving realistic security-constrained optimal power flow problems." 
         arXiv preprint arXiv:2110.01669 (2021).
"""
def cnst_pr_kg1_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.pg_kg[g,k] + m.rho_kg[g,k] == m.pg[g] + m.n_kg[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g])

def cnst_pr_kg2_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.rho_kg[g,k] * (m.pgmax[g]-m.pg_kg[g,k]) <= m.eps * (m.pgmax[g]-m.pgmin[g]) * (m.pgmax[g]-m.pgmin[g])

def cnst_pr_ke1_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.pg_ke[g,k] + m.rho_ke[g,k] == m.pg[g] + m.n_ke[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g])

def cnst_pr_ke2_exp(m, g, k):
    if g == k:
        return pyo.Constraint.Skip
    else:
        return m.rho_ke[g,k] * (m.pgmax[g]-m.pg_ke[g,k]) <= m.eps * (m.pgmax[g]-m.pgmin[g]) * (m.pgmax[g]-m.pgmin[g])

def cnst_power_bal_ptdf_kg_exp(m, k):
    return quicksum(m.pd[l] for l in m.L) == quicksum(m.pg_kg[g,k] for g in m.G)

def cnst_power_bal_ptdf_ke_exp(m, k):
    return quicksum(m.pd[l] for l in m.L) == quicksum(m.pg_ke[g,k] for g in m.G)
