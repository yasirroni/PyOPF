from typing import Dict, Any, Tuple
import numpy as np
from scipy.sparse import coo_array
from scipy.linalg import solve_triangular, ldl    

def compute_ptdf(network:Dict[str,Any]) ->  Tuple[Dict[str,Any], Dict[str,Any]]:
    S_br = compute_branch_susceptance_matrix(network).toarray() # ExB
    S_b = compute_bus_susceptance_matrix(network).toarray() # BxB
    I_g = compute_generator_incidence_matrix(network).toarray() # BxG
    I_l = compute_load_incidence_matrix(network).toarray() # BxL
    
    buses = network['bus']
    busids = sorted(list(buses.keys()))
    slack = [ buses[busid]['index'] for busid in busids if buses[busid]['bus_type'] == 3]
    if len(slack) != 1:
        raise ValueError(f'The number of slack buses should be 1. But it is now {len(slack)}.')

    return _compute_ptdf(S_br, S_b, I_g, I_l, slack)


def _compute_ptdf(S_br, S_b, I_g, I_l, slack):
    # for the slack bus, zeroing the bus susceptance entries.
    S_b[:,slack[0]] = 0.
    S_b[slack[0],:] = 0.
    S_b[slack[0],slack[0]] = 1.

    # LDLT decomposition
    L, D, perm = ldl(S_b, lower=True) 
    L = L[perm,:]
    D = np.diag(D)[perm]
    D_inv = np.diag(1./D)

    # solve for I_g
    y_g = solve_triangular(L, I_g, lower=True)
    y_g = D_inv @ y_g
    x_g = solve_triangular(L.T, y_g, lower=False)

    # solve for I_l
    y_l = solve_triangular(L, I_l, lower=True)
    y_l = D_inv @ y_l
    x_l = solve_triangular(L.T, y_l, lower=False)
    
    x_g[slack[0],:] = 0.
    x_l[slack[0],:] = 0.

    # compute ptdf for gen and load
    ptdf_g = S_br @ x_g
    ptdf_l = S_br @ x_l
    return ptdf_g, ptdf_l



def compute_branch_susceptance_matrix(network):
    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    buses = network['bus']

    E = len(branchids)
    B = len(buses)

    row, col, data = [], [], []
    for bi, branch_id in enumerate(branchids):
        branch = branches[branch_id]
        f_bus_id = branch['f_bus']
        t_bus_id = branch['t_bus']
        f_bus_idx = buses[f_bus_id]['index']
        t_bus_idx = buses[t_bus_id]['index']
        r = branch['br_r']
        x = branch['br_x']
        b = -x / (r**2 + x**2) # susceptance
        row.append(bi); col.append(f_bus_idx); data.append(b)
        row.append(bi); col.append(t_bus_idx); data.append(-b)
    
    row = np.asarray(row)
    col = np.asarray(col)
    data = np.asarray(data)
    return coo_array((data,(row,col)), shape=(E, B))


def compute_bus_susceptance_matrix(network):
    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    buses = network['bus']

    B = len(buses)

    row, col, data = [], [], []
    for bi, branch_id in enumerate(branchids):
        branch = branches[branch_id]
        f_bus_id = branch['f_bus']
        t_bus_id = branch['t_bus']
        f_bus_idx = buses[f_bus_id]['index']
        t_bus_idx = buses[t_bus_id]['index']
        r = branch['br_r']
        x = branch['br_x']
        b = -x / (r**2 + x**2) # susceptance
        row.append(f_bus_idx); col.append(t_bus_idx); data.append(-b)
        row.append(t_bus_idx); col.append(f_bus_idx); data.append(-b)
        row.append(f_bus_idx); col.append(f_bus_idx); data.append(b)
        row.append(t_bus_idx); col.append(t_bus_idx); data.append(b)

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.asarray(data)
    return coo_array((data,(row,col)), shape=(B, B))


def compute_generator_incidence_matrix(network):
    gens = network['gen']
    buses = network['bus']
    genids_all = sorted(list(gens.keys()))
    genids = [gen_id for gen_id in genids_all if gens[gen_id]['gen_status']>0] # factor out not working generators

    G = len(genids)
    B = len(buses)

    row, col = [], []
    for i, genid in enumerate(genids):
        gen = gens[genid]
        gen_bus_id = gen['gen_bus']
        row.append(buses[gen_bus_id]['index'])
        col.append(i)

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.ones(row.shape)
    return coo_array((data,(row,col)), shape=(B,G))


def compute_load_incidence_matrix(network):
    loads = network['load']
    loadids = sorted(list(loads.keys()))
    buses = network['bus']

    L = len(loads)
    B = len(buses)

    row, col = [], []
    for i, loadid in enumerate(loadids):
        busid = loads[loadid]['load_bus']
        row.append(buses[busid]['index'])
        col.append(loads[loadid]['index'])

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.ones(row.shape)
    return coo_array((data,(row,col)), shape=(B,L))