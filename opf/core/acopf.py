from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np
import math

from .base import NormalOPFModel
from .acopf_exp import *


class ACOPFModel(NormalOPFModel):
    """ AC-OPF optimization model class.  
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None:
        """ Define the (abstract) AC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        
        self.model.B = pyo.Set() # bus indices
        self.model.G = pyo.Set() # generator indices
        self.model.E = pyo.Set() # branch indices
        self.model.L = pyo.Set() # load indices
        self.model.S = pyo.Set() # shunt indices
        self.model.slack = pyo.Set() # the slack buses
        self.model.ncost = pyo.Set() # the number of costs

        self.model.gen_per_bus = pyo.Set(self.model.B, within=self.model.G)
        self.model.load_per_bus = pyo.Set(self.model.B, within=self.model.L)
        self.model.branch_in_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.branch_out_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.shunt_per_bus = pyo.Set(self.model.B, within=self.model.S)

        # ====================
        # I.    Parameters
        # ====================
        self.model.pg_init = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qg_init = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.vm_init = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.va_init = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.pf_from_init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.pf_to_init   = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.qf_from_init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.qf_to_init   = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.vmmin = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.vmmax = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.dvamin = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.dvamax = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.qd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)

        self.model.gs = pyo.Param(self.model.S, within=pyo.Reals, mutable=True)
        self.model.bs = pyo.Param(self.model.S, within=pyo.Reals, mutable=True)

        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)

        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.bus_from = pyo.Param(self.model.E, within=self.model.B)
        self.model.bus_to = pyo.Param(self.model.E, within=self.model.B)
        self.model.g_from = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.g_to = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b_from = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b_to = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_m = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_R = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_I = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.g = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous
        self.model.qg = pyo.Var(self.model.G, initialize=self.model.qg_init, bounds=qg_bound_exp, within=pyo.Reals) # reactive generation (injection), continuous
        self.model.vm = pyo.Var(self.model.B, initialize=self.model.vm_init, bounds=vm_bound_exp, within=pyo.Reals) # voltage magnitude, continuous
        self.model.va = pyo.Var(self.model.B, initialize=self.model.va_init, within=pyo.Reals) # voltage angle, continuous

        self.model.pf_from = pyo.Var(self.model.E, initialize=self.model.pf_from_init, within=pyo.Reals) # active power flow (from), continuous
        self.model.pf_to   = pyo.Var(self.model.E, initialize=self.model.pf_to_init, within=pyo.Reals) # active power flow (to), continuous
        self.model.qf_from = pyo.Var(self.model.E, initialize=self.model.qf_from_init, within=pyo.Reals) # reactive power flow (from), continuous
        self.model.qf_to   = pyo.Var(self.model.E, initialize=self.model.qf_to_init, within=pyo.Reals) # reactive power flow (to), continuous

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Voltage Angle at Slack Bus
        # ====================
        self.model.cnst_slack_va = pyo.Constraint(self.model.slack, rule=cnst_slack_va_exp)

        # ====================
        # III.b Thermal Limits
        # ====================
        self.model.cnst_thermal_branch_from = pyo.Constraint(self.model.E, rule=cnst_thermal_branch_from_exp)
        self.model.cnst_thermal_branch_to   = pyo.Constraint(self.model.E, rule=cnst_thermal_branch_to_exp)

        # ====================
        # III.c Ohm's Law
        # ====================
        self.model.cnst_ohm_pf_from = pyo.Constraint(self.model.E, rule=cnst_ohm_pf_from_exp)
        self.model.cnst_ohm_pf_to   = pyo.Constraint(self.model.E, rule=cnst_ohm_pf_to_exp)
        self.model.cnst_ohm_qf_from = pyo.Constraint(self.model.E, rule=cnst_ohm_qf_from_exp)
        self.model.cnst_ohm_qf_to   = pyo.Constraint(self.model.E, rule=cnst_ohm_qf_to_exp)

        # ====================
        # III.d Power Balance
        # ====================
        self.model.sets_balance = pyo.BuildAction(rule=define_sets_balance_exp)
        self.model.cnst_p_balance = pyo.Constraint(self.model.B, rule=cnst_p_balance_exp)
        self.model.cnst_q_balance = pyo.Constraint(self.model.B, rule=cnst_q_balance_exp)

        # ====================
        # III.e Voltage Angle Difference
        # ====================
        self.model.cnst_dva = pyo.Constraint(self.model.E, rule=cnst_dva_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)


    def _instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel:
        """ create ConcreteModel
        """
        gens = network['gen']
        buses = network['bus']
        branches = network['branch']
        loads = network['load']
        shunts = network['shunt']

        busids = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadids = sorted(list(loads.keys()))
        shuntids = sorted(list(shunts.keys()))

        branchids = sorted(list(branches.keys()))
        genids = sorted(list(gens.keys())) 
        
        ncost = 3 # all PGLib input files have three cost coefficients
        
        gen_per_bus = { busid: [] for busid in busids }
        load_per_bus = { busid: [] for busid in busids }
        branch_in_per_bus = { busid: [] for busid in busids }
        branch_out_per_bus = { busid: [] for busid in busids }
        shunt_per_bus = { busid: [] for busid in busids }

        # Generator
        pgmax, pgmin, qgmax, qgmin = {}, {}, {}, {}
        pg, qg = {}, {}
        cost = {}
        for gen_id in genids:
            gen = gens[gen_id]
            pgmax[gen_id] = gen['pmax']
            pgmin[gen_id] = gen['pmin']
            qgmax[gen_id] = gen['qmax']
            qgmin[gen_id] = gen['qmin']
            pg[gen_id] = gen['pg']
            qg[gen_id] = gen['qg']
            cost_raw = gen['cost']
            for i in range(ncost):
                cost[(gen_id,i)] = cost_raw[i]
            gen_per_bus[gen['gen_bus']].append(gen_id)
        
        # Load
        pd, qd = {}, {}
        for load_id in loadids:
            load = loads[load_id]
            pd[load_id] = load['pd']
            qd[load_id] = load['qd']
            load_per_bus[load['load_bus']].append(load_id)

        # Shunt
        gs, bs = {}, {}
        for shunt_id in shuntids:
            shunt = shunts[shunt_id]
            gs[shunt_id] = shunt['gs']
            bs[shunt_id] = shunt['bs']
            shunt_per_bus[shunt['shunt_bus']].append(shunt_id)

        # Bus
        vmmax, vmmin = {}, {}
        vm_init_val = {}
        slack = []
        for bus_id in busids:
            bus = buses[bus_id]
            vmmax[bus_id] = bus['vmax']
            vmmin[bus_id] = bus['vmin']
            vm_init_val[bus_id] = max(bus['vmin'], 1.)
            bustype = bus['bus_type']
            if bustype == 3:
                slack.append(bus_id)
        
        # Branch
        rate_a = {}
        bus_from, bus_to = {}, {}
        g_from, g_to, b_from, b_to, T_R, T_I, T_m, g, b = {}, {}, {}, {}, {}, {}, {}, {}, {}
        dvamin, dvamax = {}, {}
        for branch_id in branchids:
            branch = branches[branch_id]
            rate_a_val = branch['rate_a']
            if rate_a_val == 0.: rate_a_val + 1e12
            rate_a[branch_id] = rate_a_val
            bus_from[branch_id] = branch['f_bus']
            bus_to[branch_id] = branch['t_bus']
            g_from[branch_id] = branch['g_fr']
            g_to[branch_id] = branch['g_to']
            b_from[branch_id] = branch['b_fr']
            b_to[branch_id] = branch['b_to']
            T_m_val = branch['tap']
            shift = branch['shift']
            T_R[branch_id] = T_m_val * math.cos(shift)
            T_I[branch_id] = T_m_val * math.sin(shift)
            T_m[branch_id] = T_m_val
            r = branch['br_r']
            x = branch['br_x']
            g[branch_id] = r / (r**2 + x**2)
            b[branch_id] = -x / (r**2 + x**2)
            dvamin[branch_id] = branch['angmin']
            dvamax[branch_id] = branch['angmax']
            branch_out_per_bus[branch['f_bus']].append(branch_id) # from buses
            branch_in_per_bus[branch['t_bus']].append(branch_id)

        if init_var is not None:
            pg_init = init_var['pg']
            qg_init = init_var['qg']
            vm_init = init_var['vm']
            va_init = init_var['va']
            pf_from_init = init_var['pf1']
            pf_to_init = init_var['pf2']
            qf_from_init = init_var['qf1']
            qf_to_init = init_var['qf2']
        else:
            pg_init = pg
            qg_init = qg
            vm_init = vm_init_val
            va_init = { id: 0. for id in busids }
            pf_from_init = { id: 0. for id in branchids }
            pf_to_init = { id: 0. for id in branchids }
            qf_from_init = { id: 0. for id in branchids }
            qf_to_init = { id: 0. for id in branchids }
                
        data = {
            'G': {None: genids},
            'B': {None: busids},
            'E': {None: branchids},
            'L': {None: loadids},
            'S': {None: shuntids},
            'pg_init': pg_init,
            'qg_init': qg_init,
            'vm_init': vm_init,
            'va_init': va_init,
            'pf_from_init': pf_from_init,
            'pf_to_init': pf_to_init,
            'qf_from_init': qf_from_init,
            'qf_to_init': qf_to_init,
            'ncost': {None: np.arange(ncost)},
            'slack': {None: slack},
            'pd': pd,
            'qd': qd,
            'gs': gs,
            'bs': bs,
            'pgmax': pgmax,
            'pgmin': pgmin,
            'qgmax': qgmax,
            'qgmin': qgmin,
            'cost': cost,
            'vmmax': vmmax,
            'vmmin': vmmin,
            'rate_a': rate_a,
            'bus_from': bus_from,
            'bus_to': bus_to,
            'g_from': g_from, 'g_to': g_to, 'b_from': b_from, 'b_to': b_to,
            'T_R': T_R, 'T_I': T_I, 'T_m': T_m, 'g':g, 'b':b,
            'dvamin': dvamin, 'dvamax': dvamax
        }

        self.model.gen_per_bus_raw = gen_per_bus
        self.model.load_per_bus_raw = load_per_bus
        self.model.branch_in_per_bus_raw = branch_in_per_bus
        self.model.branch_out_per_bus_raw = branch_out_per_bus
        self.model.shunt_per_bus_raw = shunt_per_bus
        
        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel), 
        # note that self.model is not duplicated because it is desired to be AbstractModel 
        # for taking different types of problem instances consistently.

        return instance

    
    