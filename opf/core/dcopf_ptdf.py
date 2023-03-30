from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np

from .base import NormalOPFModel
from .dcopf_exp import cnst_power_bal_ptdf_exp, cnst_pf_ptdf_exp
from .acopf_exp import pg_bound_exp, obj_cost_exp
from .ptdf import compute_ptdf


class DCOPFModelPTDF(NormalOPFModel):
    """ DC-OPF using PTDF (power transfer distribution factor) optimization model class.  
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None:
        """ Define the (abstract) DC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        self.model.B = pyo.Set() # bus indices
        self.model.G = pyo.Set() # generator indices
        self.model.E = pyo.Set() # branch indices
        self.model.L = pyo.Set() # load indices
        self.model.slack = pyo.Set() # the slack buses
        self.model.ncost = pyo.Set() # the number of costs

        # # ====================
        # # I.    Parameters
        # # ====================
        self.model.pg_init = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)
        self.model.load_injection = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Power Flow
        # ====================
        self.model.cnst_pf_ptdf = pyo.Constraint(self.model.E, rule=cnst_pf_ptdf_exp)

        # ====================
        # III.b Power Balance
        # ====================
        self.model.cnst_power_bal = pyo.Constraint(rule=cnst_power_bal_ptdf_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)


    def _instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel:
        gens = network['gen']
        buses = network['bus']
        branches = network['branch']
        loads = network['load']

        busids = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadids = sorted(list(loads.keys()))

        branchids = sorted(list(branches.keys()))
        genids = sorted(list(gens.keys())) 
        genidxs = [gens[genid]['index'] for genid in genids]
        ncost = 3 # all PGLib input files have three cost coefficients

        # Generator
        pgmax, pgmin, pg, qg, cost = {}, {}, {}, {}, {}
        for gen_id in genids:
            gen = gens[gen_id]
            pgmax[gen_id] = gen['pmax']
            pgmin[gen_id] = gen['pmin']
            pg[gen_id] = gen['pg']
            qg[gen_id] = gen['qg']
            cost_raw = gen['cost']
            for i in range(ncost):
                cost[(gen_id,i)] = cost_raw[i]

        # Load 
        pd = {}
        pdvec = np.empty((len(loadids)))
        for load_id in loadids:
            load = loads[load_id]
            pd[load_id] = load['pd']
            pdvec[load['index']] = load['pd']
        pdvec = np.asarray(pdvec)

        # Bus
        slack = []
        for bus_id in busids:
            if buses[bus_id]['bus_type'] == 3:
                slack.append(bus_id)

        # Branch
        rate_a = {}
        ang2pf = {}
        for branch_id in branchids:
            branch = branches[branch_id]
            rate_a_val = branch['rate_a']
            if rate_a_val == 0.: rate_a_val + 1e12
            rate_a[branch_id] = rate_a_val
        
        if init_var is not None:
            pg_init = init_var['pg']
        else:
            pg_init = pg

        ptdf_g_raw, ptdf_l_raw = compute_ptdf(network)

        load_injection_raw = ptdf_l_raw @ pdvec
        load_injection = {}
        for branch_id in branchids:
            load_injection[branch_id] = load_injection_raw[branches[branch_id]['index']]

        self.model.ptdf_g = {}
        
        for branch_id in branchids:
            self.model.ptdf_g[branch_id] = ptdf_g_raw[branches[branch_id]['index'],genidxs].tolist()

        data = {
            'G': {None: genids},
            'B': {None: busids},
            'E': {None: branchids},
            'L': {None: loadids},
            'slack': {None: slack},
            'pg_init': pg_init,
            'ncost': {None: np.arange(ncost)},
            'pd': pd,
            'pgmax': pgmax,
            'pgmin': pgmin,
            'cost': cost,
            'rate_a': rate_a,
            'load_injection': load_injection
        }
        
        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel)
        
        return instance