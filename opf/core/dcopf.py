from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np
import math

from .base import NormalOPFModel
from .dcopf_exp import *
from .acopf_exp import pg_bound_exp, obj_cost_exp


class DCOPFModel(NormalOPFModel):
    """ DC-OPF optimization model class.  
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

        self.model.gen_per_bus = pyo.Set(self.model.B, within=self.model.G)
        self.model.load_per_bus = pyo.Set(self.model.B, within=self.model.L)
        self.model.branch_in_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.branch_out_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.bus_per_branch = pyo.Set(self.model.E, within=self.model.B)

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
        self.model.ang2pf = pyo.Param(self.model.E, self.model.B, within=pyo.Reals, mutable=True) # branch susceptance

        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous
        self.model.va = pyo.Var(self.model.B, initialize=self.model.va_init, within=pyo.Reals) # voltage angle, continuous
        self.model.pf = pyo.Var(self.model.E, initialize=self.model.pf_init, bounds=pf_bound_exp, within=pyo.Reals) # active flow (at each branch)

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Voltage Angle at Slack Bus
        # ====================
        self.model.cnst_slack_va = pyo.Constraint(self.model.slack, rule=cnst_slack_va_exp)

        # ====================
        # III.b Setup Sets for defining the following constraints
        # ====================
        self.model.sets_balance = pyo.BuildAction(rule=define_sets_balance_exp)

        # ====================
        # III.c Define Flow
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_exp)

        # ====================
        # III.d Power Balance
        # ====================
        self.model.cnst_power_bal = pyo.Constraint(self.model.B, rule=cnst_power_bal_exp)

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
        
        ncost = 3 # all PGLib input files have three cost coefficients

        gen_per_bus = { busid: [] for busid in busids }
        load_per_bus = { busid: [] for busid in busids }
        branch_in_per_bus = { busid: [] for busid in busids }
        branch_out_per_bus = { busid: [] for busid in busids }
        bus_per_branch = { branchid: set() for branchid in branchids}

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
            gen_per_bus[gen['gen_bus']].append(gen_id)

        # Load 
        pd = {}
        for load_id in loadids:
            load = loads[load_id]
            pd[load_id] = load['pd']
            load_per_bus[load['load_bus']].append(load_id)

        # Bus
        slack = []
        for bus_id in busids:
            if buses[bus_id]['bus_type'] == 3:
                slack.append(bus_id)

        # Branch
        rate_a, dvamin, dvamax = {}, {}, {}
        ang2pf = {}
        for branch_id in branchids:
            branch = branches[branch_id]
            rate_a_val = branch['rate_a']
            if rate_a_val == 0.: rate_a_val + 1e12
            rate_a[branch_id] = rate_a_val
            dvamin[branch_id] = branch['angmin']
            dvamax[branch_id] = branch['angmax']
            f_bus = branch['f_bus']
            t_bus = branch['t_bus']
            r = branch['br_r']
            x = branch['br_x']
            b = -x / (r**2 + x**2) # susceptance
            ang2pf_f_val = ang2pf.get((branch_id,f_bus), 0.)
            ang2pf_f_val += b
            ang2pf_t_val = ang2pf.get((branch_id,t_bus), 0.)
            ang2pf_t_val -= b
            ang2pf[(branch_id,f_bus)] = ang2pf_f_val
            ang2pf[(branch_id,t_bus)] = ang2pf_t_val
            branch_out_per_bus[f_bus].append(branch_id) # from buses
            branch_in_per_bus[t_bus].append(branch_id)
            bus_per_branch[branch_id].add(f_bus)
            bus_per_branch[branch_id].add(t_bus)
        
        if init_var is not None:
            pg_init = init_var['pg']
            va_init = init_var['va']
            pf_init = init_var['pf']
        else:
            pg_init = pg
            va_init = { bus_id: 0. for bus_id in busids }
            pf_init = { branch_id: 0. for branch_id in branchids }

        data = {
            'G': {None: genids},
            'B': {None: busids},
            'E': {None: branchids},
            'L': {None: loadids},
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
        self.model.bus_per_branch_raw = bus_per_branch

        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel)
        return instance


