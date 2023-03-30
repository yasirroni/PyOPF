""" parse PGLib[https://github.com/power-grid-lib/pglib-opf], which uses the format of MATPOWER.
"""
import re
from typing import List, Dict, Any, Tuple


MP_BUS_COLUMNS = [
    ("bus_i", int),
    ("bus_type", int),
    ("pd", float), ("qd", float),
    ("gs", float), ("bs", float),
    ("area", int),
    ("vm", float), ("va", float),
    ("base_kv", float),
    ("zone", int),
    ("vmax", float), ("vmin", float),
    ("lam_p", float), ("lam_q", float),
    ("mu_vmax", float), ("mu_vmin", float)
]

MP_GEN_COLUMNS = [
    ("gen_bus", str),
    ("pg", float), ("qg", float),
    ("qmax", float), ("qmin", float),
    ("vg", float),
    ("mbase", float),
    ("gen_status", int),
    ("pmax", float), ("pmin", float),
    ("pc1", float),
    ("pc2", float),
    ("qc1min", float), ("qc1max", float),
    ("qc2min", float), ("qc2max", float),
    ("ramp_agc", float),
    ("ramp_10", float),
    ("ramp_30", float),
    ("ramp_q", float),
    ("apf", float),
    ("mu_pmax", float), ("mu_pmin", float),
    ("mu_qmax", float), ("mu_qmin", float)
]

MP_BRANCH_COLUMNS = [
    ("f_bus", str),
    ("t_bus", str),
    ("br_r", float), ("br_x", float),
    ("br_b", float),
    ("rate_a", float),
    ("rate_b", float),
    ("rate_c", float),
    ("tap", float), ("shift", float),
    ("br_status", int),
    ("angmin", float), ("angmax", float),
    ("pf", float), ("qf", float),
    ("pt", float), ("qt", float),
    ("mu_sf", float), ("mu_st", float),
    ("mu_angmin", float), ("mu_angmax", float)
]

def parse_matpower(lines: List[str]) -> Dict[str,Any]:
    """ parse MATPOWER formatted m-file. The field 'mpc.areas' is excluded because it is not used in AC-OPF.

    Args:
        lines (List[str]): list of strings

    Returns:
        Dict[str,Any]: powermodel parsed dictionary structure
    """

    data = {
        'source_type': 'matpower',
        'name': None,
        'version': None,
        'baseMVA': None
    }
    data["source_type"] = "matpower"

    nlines = len(lines)
    lineidx = 0
    while lineidx < nlines:
        # print(lineidx)
        line = lines[lineidx]
        if len(line) <= 0 or line == '\n' or line == ' \n' or line[0] == '%': # exclude comments
            lineidx += 1
            continue
        elif 'function mpc' in line:
            data['name'] = line[line.find('=')+2:line.rfind('\n')]
            lineidx += 1
        elif 'mpc.version' in line:
            data['version'] = int(line[line.find('=')+3:line.rfind(';')-1])
            lineidx += 1
        elif 'mpc.baseMVA' in line:
            data['baseMVA'] = float(line[line.find('=')+2:line.rfind(';')])
            lineidx += 1
        elif 'mpc.bus' in line:
            buses, lineidx = _extract_mp_data(lines, lineidx, MP_BUS_COLUMNS, 'bus')
            data['bus'] = buses
        elif 'mpc.gencost' in line:
            gencosts, lineidx = _extract_mp_gencost_data(lines, lineidx)
            data['gencost'] = gencosts
        elif 'mpc.gen' in line:
            gens, lineidx = _extract_mp_data(lines, lineidx, MP_GEN_COLUMNS, 'gen')
            data['gen'] = gens
        elif 'mpc.branch' in line:
            branches, lineidx = _extract_mp_data(lines, lineidx, MP_BRANCH_COLUMNS, 'branch')
            data['branch'] = branches
        else:
            lineidx += 1

    return data


def _extract_mp_data(lines:List[str], lineidx:int, column_info:List[Tuple[str,...]], entry_type:str) -> List[Any]:
    entries = []
    idx = lineidx+1 
    
    entry_id = 1
    while True:
        line = lines[idx]
        if ']' in line: break
        entry = {}
        line = line[:line.rfind(';')]  # exclude ';', any comments at each line, and '\n'
        row_data = line.split()
        for i, row in enumerate(row_data):
            entry[column_info[i][0]] = column_info[i][1](row)
        
        if entry_type == 'bus':
            entry['id'] = int(row_data[0])
        else:
            entry['id'] = entry_id
        entries.append(entry)
        entry_id += 1
        idx += 1

    return entries, idx+1


def _extract_mp_gencost_data(lines:List[str], lineidx:int) -> List[Any]:
    entries = []
    idx = lineidx+1

    entry_id = 1
    while True:
        line = lines[idx]
        if ']' in line: break
        line = lines[idx]
        line = line[:line.rfind(';')]
        row_data = line.split()
        model = int(row_data[0])
        if model != 2:
            raise ValueError("Generator cost model {} is not supported. It should be model=2.".format(model))
        startup = float(row_data[1])
        shutdown = float(row_data[2])
        ncost = int(row_data[3])
        costs = [float(row_data[4+c]) for c in range(ncost)]
        entry = {
            'id': entry_id,
            # 'source_id': ["gencost", entry_idx],
            'model': model,
            'startup': startup,
            'shutdown': shutdown,
            'cost': costs
        }
        entries.append(entry)
        entry_id += 1
        idx += 1

    return entries, idx+1


def mp2data(mp_data:Dict[str,Any]) -> Dict[str,Any]:
    """ convert matpower raw data into the dictionary for analysis
    loading the entries for switch, storage, dcline are not implemented.

    Args:
        mp_data (Dict[str,Any]): matpower raw data dictionary

    Returns:
        Dict[str,Any]: data dictionary for analysis
    """
    data = {**mp_data}
    
    _mp2data_bus(data)
    _mp2data_branch(data)
    _merge_cost_data(data)

    _split_loads_shunts(data)

    _list2dict(data)

    for optional in ["load", "shunt"]:
        if len(data[optional]) == 0:
            data[optional] = {}
       
    return data


def _mp2data_bus(data):
    ...
    # buses = data['bus']
    # busids = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
    # for idx, busid in busids:
    #     buses[busid]['index'] = idx


def _mp2data_branch(data):
    branches = data["branch"]
    for branch in branches:
        if branch["tap"] == 0.0:
            branch["transformer"] = False
            branch["tap"] = 1.0
        else:
            branch["transformer"] = True
        
        branch["g_fr"] = 0.0
        branch["g_to"] = 0.0

        branch["b_fr"] = branch["br_b"] / 2.0
        branch["b_to"] = branch["br_b"] / 2.0

        del branch['br_b']

        if branch["rate_a"] == 0.0:
            del branch['rate_a']
        if branch["rate_b"] == 0.0:
            del branch['rate_b']
        if branch["rate_c"] == 0.0:
            del branch['rate_c']
    

    return None
    
def _merge_cost_data(data):
    # merges generator cost functions into generator data, if costs exist
    gen = data['gen']
    gencost = data['gencost']

    if len(gen) != len(gencost):
        if len(gen) < len(gencost):
            raise RuntimeWarning(f"The last {len(gencost)-len(gen)} generator cost records will be ignored due to too few generator records.")
            gencost = gencost[:len(gen)]
        else:
            raise RuntimeWarning(f"The number of generators ({len(gen)})is higher than the number of generator cost records ({len(gencost)})")

    for (i, gc) in enumerate(gencost):
        g = gen[i]
        # assert g['index'] == gc['index']
        assert g['id'] == gc['id']
        # del gc['index']
        del gc['id']
        # del gc['source_id']
        g.update(gc)
    
    del data['gencost'] # delete gencost from data
        


def _split_loads_shunts(data):
    data['load'], data['shunt'] = [], []

    load_id, shunt_id = 1, 1

    for i,bus in enumerate(data['bus']):
        if bus['pd'] != 0. or bus['qd'] != 0.: # load
            data['load'].append({
                'pd':        bus['pd'],
                'qd':        bus['qd'],
                'load_bus':  str(bus['bus_i']),
                'status':    int(bus['bus_type']!=4),
                'id':        load_id,
            })
            load_id += 1
        
        if bus['gs'] != 0. or bus['bs'] != 0.: #shunt
            data['shunt'].append({
                'gs': bus['gs'],
                'bs': bus['bs'],
                'shunt_bus': bus['bus_i'],
                'status': int(bus['bus_type']!=4),
                'id':    shunt_id
            })
            shunt_id += 1

        for k in ["pd", "qd", "gs", "bs"]:
            del bus[k]
    
    return None

def _list2dict(data):
    keys = ['gen', 'load', 'shunt', 'branch', 'bus']

    for k in keys:
        entries = data[k]
        entries_dict = {}
        for i,entry in enumerate(entries):
            # idx = entry.get('index',i)
            # assert idx not in entries_dict
            # entries_dict[idx] = entry
            id = entry.get('id', i)
            assert id not in entries_dict
            entries_dict[str(id)] = entry
        data[k] = entries_dict # convert list to dict


