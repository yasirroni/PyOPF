from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np
import math

from .base import AbstractPowerBaseModel
from .dcopf_exp import *


class AbstractDCOPFModel(AbstractPowerBaseModel):
    """ Abstract DC-OPF optimization model class.  
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None:
        """ Define the (abstract) DC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        print('build model...', end=' ')
        self.model.B = pyo.Set() # bus indices
        self.model.G = pyo.Set() # generator indices
        self.model.E = pyo.Set() # branch indices
        self.model.L = pyo.Set() # load indices
        self.model.slack = pyo.Set() # the slack buses
        self.model.ncost = pyo.Set() # the number of costs

        self.model.gen_per_bus = pyo.Set(self.model.B, within=self.model.G)
        self.model.load_per_bus = pyo.Set(self.model.B, within=self.model.L)
        self.model.branch_in_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.branch_out_per_bus = pyo.Set(self.model.B, within=self.model.E)

        # # ====================
        # # I.    Parameters
        # # ====================
        self.model.pg_init = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.va_init = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.pf_init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.ang2pf = pyo.Param(self.model.E, self.model.B, within=pyo.Reals, default=0., mutable=True) # branch susceptance

        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, within=pyo.Reals) # active generation (injection), continuous
        self.model.va = pyo.Var(self.model.B, initialize=self.model.va_init, within=pyo.Reals) # voltage angle, continuous
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
        # III.b Voltage Angle at Slack Bus
        # ====================
        self.model.cnst_slack_va = pyo.Constraint(self.model.slack, rule=cnst_slack_va_exp)

        # ====================
        # III.c Define Flow
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_exp)

        # ====================
        # III.d Power Balance
        # ====================
        self.model.sets_balance = pyo.BuildAction(rule=define_sets_balance_exp)
        self.model.cnst_power_bal = pyo.Constraint(self.model.B, rule=cnst_power_bal_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)
        print('end')


    def instantiate_model(self, network:Dict[str,Any], init_var:Dict[str,Any] = None) -> pyo.ConcreteModel:
        print('instantiate model...', end=' ')
        gens = network['gen']
        buses = network['bus']
        branches = network['branch']
        loads = network['load']

        busidxs = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadidxs = sorted(list(loads.keys()))

        branchidxs_all = sorted(list(branches.keys()))
        branchidxs = [branch_idx for branch_idx in branchidxs_all if branches[branch_idx]['br_status']>0] # factor out not working branches
        genidxs_all = sorted(list(gens.keys())) 
        genidxs = [gen_idx for gen_idx in genidxs_all if gens[gen_idx]['gen_status']>0] # factor out not working generators

        ncost = 3 # all PGLib input files have three cost coefficients

        gen_per_bus = { busidx: [] for busidx in busidxs }
        load_per_bus = { busidx: [] for busidx in busidxs }
        branch_in_per_bus = { busidx: [] for busidx in busidxs }
        branch_out_per_bus = { busidx: [] for busidx in busidxs }

        # Generator
        pgmax, pgmin, pg, qg, cost = {}, {}, {}, {}, {}
        for gen_idx in genidxs:
            gen = gens[gen_idx]
            pgmax[gen_idx] = gen['pmax']
            pgmin[gen_idx] = gen['pmin']
            pg[gen_idx] = gen['pg']
            qg[gen_idx] = gen['qg']
            cost_raw = gen['cost']
            for i in range(ncost):
                cost[(gen_idx,i)] = cost_raw[i]
            gen_per_bus[gen['gen_bus']].append(gen_idx)

        # Load 
        pd = {}
        for load_idx in loadidxs:
            load = loads[load_idx]
            pd[load_idx] = load['pd']
            load_per_bus[load['load_bus']].append(load_idx)

        # Bus
        slack = []
        for bus_idx in busidxs:
            if buses[bus_idx]['bus_type'] == 3:
                slack.append(bus_idx)

        # Branch
        rate_a, dvamin, dvamax = {}, {}, {}
        ang2pf = {}
        for branch_idx in branchidxs:
            branch = branches[branch_idx]
            rate_a_val = branch['rate_a']
            if rate_a_val == 0.: rate_a_val + 1e12
            rate_a[branch_idx] = rate_a_val
            dvamin[branch_idx] = branch['angmin']
            dvamax[branch_idx] = branch['angmax']
            f_bus = branch['f_bus']
            t_bus = branch['t_bus']
            r = branch['br_r']
            x = branch['br_x']
            b = -x / (r**2 + x**2) # susceptance
            ang2pf_f_val = ang2pf.get((branch_idx,f_bus), 0.)
            ang2pf_f_val += b
            ang2pf_t_val = ang2pf.get((branch_idx,t_bus), 0.)
            ang2pf_t_val -= b
            ang2pf[(branch_idx,f_bus)] = ang2pf_f_val
            ang2pf[(branch_idx,t_bus)] = ang2pf_t_val
            branch_out_per_bus[branch['f_bus']].append(branch_idx) # from buses
            branch_in_per_bus[branch['t_bus']].append(branch_idx)
        
        if init_var is not None:
            pg_init = init_var['pg']
            va_init = init_var['va']
            pf_init = init_var['pf']
        else:
            pg_init = pg
            va_init = { idx: 0. for idx in busidxs }
            pf_init = { idx: 0. for idx in branchidxs }


        data = {
            'G': {None: genidxs},
            'B': {None: busidxs},
            'E': {None: branchidxs},
            'L': {None: loadidxs},
            'slack': {None: slack},
            'pg_init': pg_init,
            'va_init': va_init,
            'pf_init': pf_init,
            'ncost': {None: np.arange(ncost)},
            'pd': pd,
            'pgmax': pgmax,
            'pgmin': pgmin,
            'cost': cost,
            'rate_a': rate_a,
            'ang2pf': ang2pf,
            'dvamin': dvamin, 'dvamax': dvamax
        }

        self.model.gen_per_bus_raw = gen_per_bus
        self.model.load_per_bus_raw = load_per_bus
        self.model.branch_in_per_bus_raw = branch_in_per_bus
        self.model.branch_out_per_bus_raw = branch_out_per_bus

        instance = self.model.create_instance({None: data}) # create instance (ConcreteModel), 
        instance.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) # define the dual assess point
        print('end')
        return instance


