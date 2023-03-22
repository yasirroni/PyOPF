from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np
import math

from .base import AbstractPowerBaseModel
from .dcopf_exp import *
from .dcopf_ptdf_exp import *
from .utils import compute_ptdf

class AbstractDCOPFModelPTDF(AbstractPowerBaseModel):
    """ Abstract DC-OPF using PTDF (power transfer distribution factor) optimization model class.  
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None:
        """ Define the (abstract) DC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        print('build model...', end=' ', flush=True)
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
        self.model.pf_init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)
        self.model.load_injection = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, within=pyo.Reals) # active generation (injection), continuous
        self.model.pf = pyo.Var(self.model.E, initialize=self.model.pf_init, within=pyo.Reals) # active flow (at each branch)

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a     Bounds
        # ====================
        self.model.cnst_pg_bound_min = pyo.Constraint(self.model.G, rule=cnst_pg_bound_min_exp)
        self.model.cnst_pg_bound_max = pyo.Constraint(self.model.G, rule=cnst_pg_bound_max_exp)
        self.model.cnst_pf_bound_min = pyo.Constraint(self.model.E, rule=cnst_pf_bound_min_exp)
        self.model.cnst_pf_bound_max = pyo.Constraint(self.model.E, rule=cnst_pf_bound_max_exp)

        # ====================
        # III.b Define Flow
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_ptdf_exp)
        # self.model.cnst_pf = pyo.Constraint(rule=cnst_pf_ptdf_exp)

        # ====================
        # III.c Power Balance
        # ====================
        # self.model.define_injections = pyo.BuildAction(rule=define_sets_balance_exp)
        self.model.cnst_power_bal = pyo.Constraint(rule=cnst_power_bal_ptdf_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)
        print('end', flush=True)


    def instantiate_model(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel:
        print('instantiate model...', end=' ', flush=True)
        gens = network['gen']
        buses = network['bus']
        branches = network['branch']
        loads = network['load']

        busids = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadids = sorted(list(loads.keys()))

        branchids_all = sorted(list(branches.keys()))
        branchids = [branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0] # factor out not working branches
        genids_all = sorted(list(gens.keys())) 
        genids = [gen_id for gen_id in genids_all if gens[gen_id]['gen_status']>0] # factor out not working generators

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
        pdvec = []
        for load_id in loadids:
            load = loads[load_id]
            pd[load_id] = load['pd']
            pdvec.append(load['pd'])
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
            pf_init = init_var['pf']
        else:
            pg_init = pg
            pf_init = { id: 0. for id in branchids }

        ptdf_g_raw, ptdf_l_raw = compute_ptdf(network)
        load_injection_raw = ptdf_l_raw @ pdvec
        load_injection = {}
        for i, branch_id in enumerate(branchids):
            load_injection[branch_id] = load_injection_raw[i]

        self.model.ptdf_g = {}
        for i, branchid in enumerate(branchids):
            self.model.ptdf_g[branchid] = ptdf_g_raw[i,:].tolist()

        data = {
            'G': {None: genids},
            'B': {None: busids},
            'E': {None: branchids},
            'L': {None: loadids},
            'slack': {None: slack},
            'pg_init': pg_init,
            'pf_init': pf_init,
            'ncost': {None: np.arange(ncost)},
            'pd': pd,
            'pgmax': pgmax,
            'pgmin': pgmin,
            'cost': cost,
            'rate_a': rate_a,
            'load_injection': load_injection
        }
        
        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel)
        instance.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) # define the dual assess point
        print('end', flush=True)
        return instance