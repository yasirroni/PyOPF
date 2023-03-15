import pyomo.environ as pyo

def cnst_pg_bound_min_exp(m, g):
    return m.pgmin[g] - m.pg[g] <= 0. 

def cnst_pg_bound_max_exp(m, g):
    return m.pg[g] - m.pgmax[g] <= 0. 

def cnst_qg_bound_min_exp(m, g):
    return m.qgmin[g] - m.qg[g] <= 0. 

def cnst_qg_bound_max_exp(m, g):
    return m.qg[g] - m.qgmax[g] <= 0. 

def cnst_vm_bound_min_exp(m, b):
    return m.vmmin[b] - m.vm[b] <= 0. 

def cnst_vm_bound_max_exp(m, b):
    return m.vm[b] - m.vmmax[b] <= 0. 

def cnst_slack_va_exp(m, s):
    return m.va[s] == 0.

def cnst_thermal_branch_from_exp(m, e):
    return m.pf1[e]**2 + m.qf1[e]**2 - m.rate_a[e]**2 <= 0.

def cnst_thermal_branch_to_exp(m, e):
    return m.pf2[e]**2 + m.qf2[e]**2 - m.rate_a[e]**2 <= 0.

def cnst_ohm_pf1_exp(m, e):
    return m.pf1[e] == (1/m.T_m[e]**2) * (m.g[e] + m.g1[e]) * m.vm[m.f_bus[e]]**2\
        + ((-m.g[e] * m.T_R[e] + m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.cos(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])\
        + ((-m.b[e] * m.T_R[e] - m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.sin(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])

def cnst_ohm_pf2_exp(m, e):
    return m.pf2[e] == (m.g[e] + m.g2[e]) * m.vm[m.t_bus[e]]**2\
                + ((-m.g[e] * m.T_R[e] - m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.cos(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])\
                + ((-m.b[e] * m.T_R[e] + m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.sin(-m.va[m.f_bus[e]] + m.va[m.t_bus[e]])

def cnst_ohm_qf1_exp(m, e):
    return m.qf1[e] == - (1/m.T_m[e]**2) * (m.b[e] + m.b1[e]) * m.vm[m.f_bus[e]]**2\
                - ((-m.b[e] * m.T_R[e] - m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.cos(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])\
                + ((-m.g[e] * m.T_R[e] + m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.sin(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])

def cnst_ohm_qf2_exp(m, e):
    return m.qf2[e] == -(m.b[e] + m.b2[e]) * m.vm[m.t_bus[e]]**2\
                - ((-m.b[e] * m.T_R[e] + m.g[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.cos(m.va[m.f_bus[e]] - m.va[m.t_bus[e]])\
                + ((-m.g[e] * m.T_R[e] - m.b[e] * m.T_I[e])/m.T_m[e]**2) * (m.vm[m.f_bus[e]] * m.vm[m.t_bus[e]]) * pyo.sin(-m.va[m.f_bus[e]] + m.va[m.t_bus[e]])
            
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
    
    for busidx, shuntlist in m.shunt_per_bus_raw.items():
        if len(shuntlist) > 0:
            for shuntidx in shuntlist:
                m.shunt_per_bus[busidx].add(shuntidx)

def cnst_p_balance_exp(m, b):
    return sum(m.pg[g] for g in m.gen_per_bus[b])\
            - sum(m.pf2[e] for e in m.branch_in_per_bus[b])\
            - sum(m.pd[l] for l in m.load_per_bus[b])\
            - sum(m.pf1[e] for e in m.branch_out_per_bus[b])\
            - sum(m.gs[s] for s in m.shunt_per_bus[b]) * m.vm[b]**2 \
            == 0.

def cnst_q_balance_exp(m, b):
    return sum(m.qg[g] for g in m.gen_per_bus[b])\
            - sum(m.qf2[e] for e in m.branch_in_per_bus[b])\
            - sum(m.qd[l] for l in m.load_per_bus[b])\
            - sum(m.qf1[e] for e in m.branch_out_per_bus[b])\
            + sum(m.bs[s] for s in m.shunt_per_bus[b]) * m.vm[b]**2\
            == 0.
            
def cnst_vad_lower_exp(m, e):
    return m.angmin[e] - (m.va[m.f_bus[e]] - m.va[m.t_bus[e]]) <= 0.

def cnst_vad_upper_exp(m, e):
    return m.va[m.f_bus[e]] - m.va[m.t_bus[e]] - m.angmax[e] <= 0.

def obj_cost_exp(m, g):
    return sum(m.pg[g]*m.pg[g]*m.cost[g,0] + m.pg[g]*m.cost[g,1] + m.cost[g,2] for g in m.G)
