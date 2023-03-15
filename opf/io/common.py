
import math

def _apply_func(data, key, func):
    if key in data:
        data[key] = func(data[key])

def make_per_unit(data):
    mva_base = data["baseMVA"]
    ka_base = mva_base
    rescale        = lambda x: x/mva_base
    rescale_dual   = lambda x: x*mva_base
    rescale_ampere = lambda x: x/ka_base
    deg2rad = math.radians

    if 'bus' in data:
        for bus_idx, bus in data['bus'].items():
            _apply_func(bus, 'va', deg2rad)
            _apply_func(bus, "lam_kcl_r", rescale_dual)
            _apply_func(bus, "lam_kcl_i", rescale_dual)
    
    if 'load' in data:
        for load_idx, load in data['load'].items():
            _apply_func(load, 'pd', rescale)
            _apply_func(load, 'qd', rescale)

    if 'shunt' in data:
        for shunt_idx, shunt in data['shunt'].items():
            _apply_func(shunt, 'gs', rescale)
            _apply_func(shunt, 'bs', rescale)

    if 'gen' in data:
        for gen_idx, gen in data['gen'].items():
            _apply_func(gen, 'pg', rescale)
            _apply_func(gen, 'qg', rescale) 

            _apply_func(gen, 'pmax', rescale)
            _apply_func(gen, 'pmin', rescale)

            _apply_func(gen, 'qmax', rescale)
            _apply_func(gen, 'qmin', rescale)

            _apply_func(gen, 'ramp_agc', rescale)
            _apply_func(gen, 'ramp_10', rescale)
            _apply_func(gen, 'ramp_30', rescale)
            _apply_func(gen, 'ramp_q', rescale)
            _rescale_cost(gen, mva_base)

    if 'branch' in data:
        for branch_idx, branch in data['branch'].items():
            _apply_func(branch, "rate_a", rescale)
            _apply_func(branch, "rate_b", rescale)
            _apply_func(branch, "rate_c", rescale)

            _apply_func(branch, "c_rating_a", rescale_ampere)
            _apply_func(branch, "c_rating_b", rescale_ampere)
            _apply_func(branch, "c_rating_c", rescale_ampere)

            _apply_func(branch, "shift", deg2rad)
            _apply_func(branch, "angmax", deg2rad)
            _apply_func(branch, "angmin", deg2rad)

            _apply_func(branch, "pf", rescale)
            _apply_func(branch, "pt", rescale)
            _apply_func(branch, "qf", rescale)
            _apply_func(branch, "qt", rescale)

            _apply_func(branch, "mu_sm_fr", rescale_dual)
            _apply_func(branch, "mu_sm_to", rescale_dual)

            _apply_func(branch, "ta_max", deg2rad)
            _apply_func(branch, "ta_min", deg2rad)


def _rescale_cost(gen, scale):
    assert 'model' in gen and gen['model'] == 2
    degree = len(gen['cost'])
    for i,item in enumerate(gen['cost']):
        gen['cost'][i] = (scale**(degree-i-1))*item
        gen['ncost'] = degree


# def simplify_cost_terms(data):
#     # TODO: not useful?? recheck it with ncost in pyomo model
#     if 'gen' in data:
#         for gen_idx, gen in data['gen'].items():
#             cost = gen['cost']
#             if cost[0] == 0.:
#                 cost = cost[1:]
#             ncost = len(cost)
#             gen['ncost'] = ncost
#             gen['cost'] = cost