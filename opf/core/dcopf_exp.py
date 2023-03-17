import pyomo.environ as pyo
from pyomo.core.util import quicksum

def cnst_pg_bound_min_exp(m, g):
    return m.pgmin[g] - m.pg[g] <= 0. 

def cnst_pg_bound_max_exp(m, g):
    return m.pg[g] - m.pgmax[g] <= 0. 

def cnst_pf_bound_min_exp(m, e):
    return -m.rate_a[e] - m.pf[e] <= 0.

def cnst_pf_bound_max_exp(m, e):
    return m.pf[e] - m.rate_a[e] <= 0.

def cnst_slack_va_exp(m, s):
    return m.va[s] == 0.

def cnst_pf_exp(m, e):
    return m.pf[e] - quicksum(m.ang2pf[e,b]*m.va[b] for b in m.B) == 0.

def define_sets_balance_exp(m):
    for busidx, genlist in m.gen_per_bus_raw.items():
        if len(genlist) > 0:
            for genidx in genlist:
                m.gen_per_bus[busidx].add(genidx)

    for busidx, loadlist in m.load_per_bus_raw.items():
        if len(loadlist) > 0:
            for loadidx in loadlist:
                m.load_per_bus[busidx].add(loadidx)

    for busidx, branchlist in m.branch_in_per_bus_raw.items():
        if len(branchlist) > 0:
            for branchidx in branchlist:
                m.branch_in_per_bus[busidx].add(branchidx)
    
    for busidx, branchlist in m.branch_out_per_bus_raw.items():
        if len(branchlist) > 0:
            for branchidx in branchlist:
                m.branch_out_per_bus[busidx].add(branchidx)

def cnst_power_bal_exp(m, b):
    return quicksum(m.pf[e] for e in m.branch_out_per_bus[b]) - quicksum(m.pf[e] for e in m.branch_in_per_bus[b])\
            - quicksum(m.pg[g] for g in m.gen_per_bus[b]) + quicksum(m.pd[l] for l in m.load_per_bus[b]) == 0.

def obj_cost_exp(m, g):
    return quicksum(m.pg[g]*m.pg[g]*m.cost[g,0] + m.pg[g]*m.cost[g,1] + m.cost[g,2] for g in m.G)