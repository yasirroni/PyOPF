from typing import Dict, Any, Tuple
import numpy as np
from scipy.sparse import csc_array


def compute_branch_susceptance_matrix(network):
    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    buses = network['bus']

    E = len(branchids)
    B = len(buses)

    row, col, data = [], [], []
    for branch_id in branchids:
        branch = branches[branch_id]
        branch_idx = branch['index']
        f_bus_id = branch['f_bus']
        t_bus_id = branch['t_bus']
        f_bus_idx = buses[f_bus_id]['index']
        t_bus_idx = buses[t_bus_id]['index']
        r = branch['br_r']
        x = branch['br_x']
        b = -x / (r**2 + x**2) # susceptance
        row.append(branch_idx); col.append(f_bus_idx); data.append(b)
        row.append(branch_idx); col.append(t_bus_idx); data.append(-b)
    
    row = np.asarray(row)
    col = np.asarray(col)
    data = np.asarray(data)
    return csc_array((data,(row,col)), shape=(E, B))


def compute_bus_susceptance_matrix(network, slack_idx):
    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    buses = network['bus']

    B = len(buses)

    row, col, data = [], [], []
    for branch_id in branchids:
        branch = branches[branch_id]
        f_bus_id = branch['f_bus']
        t_bus_id = branch['t_bus']
        f_bus_idx = buses[f_bus_id]['index']
        t_bus_idx = buses[t_bus_id]['index']
        r = branch['br_r']
        x = branch['br_x']
        b = -x / (r**2 + x**2) # susceptance
        if t_bus_idx is not slack_idx and f_bus_idx is not slack_idx:
            row.append(f_bus_idx); col.append(t_bus_idx); data.append(-b)
            row.append(t_bus_idx); col.append(f_bus_idx); data.append(-b)
        if f_bus_idx is not slack_idx:
            row.append(f_bus_idx); col.append(f_bus_idx); data.append(b)
        if t_bus_idx is not slack_idx:
            row.append(t_bus_idx); col.append(t_bus_idx); data.append(b)

    row.append(slack_idx); col.append(slack_idx); data.append(1.)

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.asarray(data)
    return csc_array((data, (row,col)), shape=(B, B))


def compute_generator_incidence_matrix(network):
    gens = network['gen']
    buses = network['bus']
    genids_all = sorted(list(gens.keys()))
    genids = [gen_id for gen_id in genids_all if gens[gen_id]['gen_status']>0] # factor out not working generators

    G = len(genids)
    B = len(buses)

    row, col = [], []
    for genid in genids:
        gen = gens[genid]
        gen_bus_id = gen['gen_bus']
        row.append(buses[gen_bus_id]['index'])
        col.append(gen['index'])

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.ones(row.shape)
    return csc_array((data,(row,col)), shape=(B,G))


def compute_load_incidence_matrix(network):
    loads = network['load']
    loadids = sorted(list(loads.keys()))
    buses = network['bus']

    L = len(loads)
    B = len(buses)

    row, col = [], []
    for loadid in loadids:
        busid = loads[loadid]['load_bus']
        row.append(buses[busid]['index'])
        col.append(loads[loadid]['index'])

    row = np.asarray(row)
    col = np.asarray(col)
    data = np.ones(row.shape)
    return csc_array((data,(row,col)), shape=(B,L))


def compute_line_incidence_matrix(network):
    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    buses = network['bus']

    E = len(branchids)
    B = len(buses)

    row, col, data = [], [], []
    for branch_id in branchids:
        branch = branches[branch_id]
        branch_idx = branch['index']
        f_bus_id = branch['f_bus']
        t_bus_id = branch['t_bus']
        f_bus_idx = buses[f_bus_id]['index']
        t_bus_idx = buses[t_bus_id]['index']
        row.append(f_bus_idx); col.append(branch_idx); data.append(1.)
        row.append(t_bus_idx); col.append(branch_idx); data.append(-1.)

    return csc_array((data, (row,col)), shape=(B,E))


def _preprocessing_network(network:Dict[str,Any]) -> None:
    if network['preprocessed']: return
    gens = network['gen']
    branches = network['branch']
    genids_all = sorted(list(gens.keys())) 
    genids = [gen_id for gen_id in genids_all if gens[gen_id]['gen_status']>0] # factor out not working generators

    branchids_all = sorted(list(branches.keys()))
    branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
    
    gens_new = {}
    for genidx, genid in enumerate(genids):
        gen = gens[genid]
        gen['index'] = genidx
        gens_new[genid] = gen
    network['gen'] = gens_new # update

    branches_new = {}
    for branchidx, branchid in enumerate(branchids):
        branch = branches[branchid]
        branch['index'] = branchidx
        branches_new[branchid] = branch
    network['branch'] = branches_new # update
    
    for busidx, (busid, bus) in enumerate(network['bus'].items()):
        bus['index'] = busidx
    
    for loadidx, (loadid, load) in enumerate(network['load'].items()):
        load['index'] = loadidx
    
    for shuntidx, (shuntid, shunt) in enumerate(network['shunt'].items()):
        shunt['index'] = shuntidx

    network['preprocessed'] = True