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
    return (-m.rate_a[e], m.pf[e] + m.m.lodf[e,k]*m.pf[k], m.rate_a[e])

def cnst_pg_kg_exp(m, k):
    return m.pg_kg[k,k] == 0.

def cnst_pr_kg1_exp(m, g, k):
    return pyo.abs(m.pg_kg[g,k]-m.pg[g]-m.n_kg[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g])) <= m.bigM * (1-m.x_kg[g,k])

def cnst_pr_kg2_exp(m, g, k):
    return m.pg[g] + m.n_kg[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g]) >= m.pgmax[g] * (1-m.x_kg[g,k])

def cnst_pr_kg3_exp(m, g, k):
    return m.pg_kg[g,k] >= m.pgmax[g] * (1-m.x_kg[g,k])

def cnst_pr_ke1_exp(m, g, k):
    return pyo.abs(m.pg_ke[g,k]-m.pg[g]-m.n_ke[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g])) <= m.bigM * (1-m.x_ke[g,k])

def cnst_pr_ke2_exp(m, g, k):
    return m.pg[g] + m.n_ke[k]*m.gamma[g]*(m.pgmax[g]-m.pgmin[g]) >= m.pgmax[g] * (1-m.x_ke[g,k])

def cnst_pr_ke3_exp(m, g, k):
    return m.pg_ke[g,k] >= m.pgmax[g] * (1-m.x_ke[g,k])