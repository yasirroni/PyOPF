import pyomo.environ as pyo
from pyomo.core.util import quicksum
import math

def pg_bound_exp(m, g):
    return (m.pgmin[g], m.pgmax[g])

def qg_bound_exp(m, g):
    return (m.qgmin[g], m.qgmax[g])

def vm_bound_exp(m, b):
    return (m.vmmin[b], m.vmmax[b])

def cnst_slack_va_exp(m, s):
    return m.va[s] == 0.

def cnst_thermal_branch_from_exp(m, e):
    return m.pf_from[e]**2 + m.qf_from[e]**2 - m.rate_a[e]**2 <= 0.

def cnst_thermal_branch_to_exp(m, e):
    return m.pf_to[e]**2 + m.qf_to[e]**2 - m.rate_a[e]**2 <= 0.

def cnst_ohm_pf_from_exp(m, e):
    return m.pf_from[e] == (1/m.T_m[e]**2) * (m.g[e] + m.g_from[e]) * m.vm[m.bus_from[e]]**2\
        + ((-m.g[e] * m.T_R[e] + m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.cos(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])\
        + ((-m.b[e] * m.T_R[e] - m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.sin(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])

def cnst_ohm_pf_to_exp(m, e):
    return m.pf_to[e] == (m.g[e] + m.g_to[e]) * m.vm[m.bus_to[e]]**2\
                + ((-m.g[e] * m.T_R[e] - m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.cos(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])\
                + ((-m.b[e] * m.T_R[e] + m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.sin(-m.va[m.bus_from[e]] + m.va[m.bus_to[e]])

def cnst_ohm_qf_from_exp(m, e):
    return m.qf_from[e] == - (1/m.T_m[e]**2) * (m.b[e] + m.b_from[e]) * m.vm[m.bus_from[e]]**2\
                - ((-m.b[e] * m.T_R[e] - m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.cos(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])\
                + ((-m.g[e] * m.T_R[e] + m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.sin(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])

def cnst_ohm_qf_to_exp(m, e):
    return m.qf_to[e] == -(m.b[e] + m.b_to[e]) * m.vm[m.bus_to[e]]**2\
                - ((-m.b[e] * m.T_R[e] + m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.cos(m.va[m.bus_from[e]] - m.va[m.bus_to[e]])\
                + ((-m.g[e] * m.T_R[e] - m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.bus_from[e]] * m.vm[m.bus_to[e]]) * pyo.sin(-m.va[m.bus_from[e]] + m.va[m.bus_to[e]])
            
def define_sets_balance_exp(m):
    for busid, genlist in m.gen_per_bus_raw.items():
        if len(genlist) > 0:
            for genid in genlist:
                m.gen_per_bus[busid].add(genid)

    for busid, loadlist in m.load_per_bus_raw.items():
        if len(loadlist) > 0:
            for loadid in loadlist:
                m.load_per_bus[busid].add(loadid)

    for busid, branchlist in m.branch_in_per_bus_raw.items():
        if len(branchlist) > 0:
            for branchid in branchlist:
                m.branch_in_per_bus[busid].add(branchid)
    
    for busid, branchlist in m.branch_out_per_bus_raw.items():
        if len(branchlist) > 0:
            for branchid in branchlist:
                m.branch_out_per_bus[busid].add(branchid)
    
    for busid, shuntlist in m.shunt_per_bus_raw.items():
        if len(shuntlist) > 0:
            for shuntid in shuntlist:
                m.shunt_per_bus[busid].add(shuntid)

def cnst_p_balance_exp(m, b):
    return quicksum(m.pg[g] for g in m.gen_per_bus[b])\
            - quicksum(m.pf_to[e] for e in m.branch_in_per_bus[b])\
            - quicksum(m.pd[l] for l in m.load_per_bus[b])\
            - quicksum(m.pf_from[e] for e in m.branch_out_per_bus[b])\
            - quicksum(m.gs[s] for s in m.shunt_per_bus[b]) * m.vm[b]**2 \
            == 0.

def cnst_q_balance_exp(m, b):
    return quicksum(m.qg[g] for g in m.gen_per_bus[b])\
            - quicksum(m.qf_to[e] for e in m.branch_in_per_bus[b])\
            - quicksum(m.qd[l] for l in m.load_per_bus[b])\
            - quicksum(m.qf_from[e] for e in m.branch_out_per_bus[b])\
            + quicksum(m.bs[s] for s in m.shunt_per_bus[b]) * m.vm[b]**2\
            == 0.
def cnst_dva_exp(m, e):
    return (m.dvamin[e], m.va[m.bus_from[e]] - m.va[m.bus_to[e]], m.dvamax[e])
    
def obj_cost_exp(m, g):
    return quicksum(m.pg[g]*m.pg[g]*m.cost[g,0] + m.pg[g]*m.cost[g,1] + m.cost[g,2] for g in m.G)
