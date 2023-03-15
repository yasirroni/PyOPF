from typing import Any, Dict
import pyomo.environ as pyo
import numpy as np
import math

from .base import AbstractPowerBaseModel
from .acopf_exp import *


class AbstractACOPFModel(AbstractPowerBaseModel):
    """ Abstract optimization model class.  
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None:
        """ Define the (abstract) AC-OPF optimization model. 
            This is enabled without having the specific parameter value.
        """
        print('build model...', end=' ')
        
        self.model.B = pyo.Set() # bus indices
        self.model.G = pyo.Set() # generator indices
        self.model.E = pyo.Set() # branch indices
        self.model.L = pyo.Set() # load indices
        self.model.S = pyo.Set() # shunt indices
        self.model.slack = pyo.Set() # the slack buses
        self.model.ncost = pyo.Set() # the number of costs  # it should be 2 (linear...)

        self.model.gen_per_bus = pyo.Set(self.model.B, within=self.model.G)
        self.model.load_per_bus = pyo.Set(self.model.B, within=self.model.L)
        self.model.branch_in_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.branch_out_per_bus = pyo.Set(self.model.B, within=self.model.E)
        self.model.shunt_per_bus = pyo.Set(self.model.B, within=self.model.S)

        # # ====================
        # # I.    Parameters
        # # ====================
        self.model.pginit = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qginit = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.vminit = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.vainit = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.pf1init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.pf2init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.qf1init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.qf2init = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.qgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.vmmin = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)
        self.model.vmmax = pyo.Param(self.model.B, within=pyo.Reals, mutable=True)

        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.qd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)

        self.model.gs = pyo.Param(self.model.S, within=pyo.Reals, mutable=True)
        self.model.bs = pyo.Param(self.model.S, within=pyo.Reals, mutable=True)

        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)

        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.f_bus = pyo.Param(self.model.E, within=self.model.B)
        self.model.t_bus = pyo.Param(self.model.E, within=self.model.B)
        self.model.g1 = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.g2 = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b1 = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b2 = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_m = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_R = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.T_I = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.g = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.b = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        self.model.angmin = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.angmax = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pginit, within=pyo.Reals) # active generation (injection), continuous
        self.model.qg = pyo.Var(self.model.G, initialize=self.model.qginit, within=pyo.Reals) # reactive generation (injection), continuous
        self.model.vm = pyo.Var(self.model.B, initialize=self.model.vminit, within=pyo.Reals) # voltage magnitude, continuous
        self.model.va = pyo.Var(self.model.B, initialize=self.model.vainit, within=pyo.Reals) # voltage angle, continuous

        self.model.pf1 = pyo.Var(self.model.E, initialize=self.model.pf1init, within=pyo.Reals) # active power flow (from), continuous
        self.model.pf2 = pyo.Var(self.model.E, initialize=self.model.pf2init, within=pyo.Reals) # active power flow (to), continuous
        self.model.qf1 = pyo.Var(self.model.E, initialize=self.model.qf1init, within=pyo.Reals) # reactive power flow (from), continuous
        self.model.qf2 = pyo.Var(self.model.E, initialize=self.model.qf2init, within=pyo.Reals) # reactive power flow (to), continuous

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a     Bounds
        # ====================
        self.model.cnst_pg_bound_min = pyo.Constraint(self.model.G, rule=cnst_pg_bound_min_exp)
        self.model.cnst_pg_bound_max = pyo.Constraint(self.model.G, rule=cnst_pg_bound_max_exp)
        self.model.cnst_qg_bound_min = pyo.Constraint(self.model.G, rule=cnst_qg_bound_min_exp)
        self.model.cnst_qg_bound_max = pyo.Constraint(self.model.G, rule=cnst_qg_bound_max_exp)
        self.model.cnst_vm_bound_min = pyo.Constraint(self.model.B, rule=cnst_vm_bound_min_exp)
        self.model.cnst_vm_bound_max = pyo.Constraint(self.model.B, rule=cnst_vm_bound_max_exp)

        # ====================
        # III.b Voltage Angle at Slack Bus
        # ====================
        self.model.cnst_slack_va = pyo.Constraint(self.model.slack, rule=cnst_slack_va_exp)

        # ====================
        # III.c Thermal Limits
        # ====================
        self.model.cnst_thermal_branch_from = pyo.Constraint(self.model.E, rule=cnst_thermal_branch_from_exp)
        self.model.cnst_thermal_branch_to   = pyo.Constraint(self.model.E, rule=cnst_thermal_branch_to_exp)

        # ====================
        # III.d Ohm's Law
        # ====================
        self.model.cnst_ohm_pf1 = pyo.Constraint(self.model.E, rule=cnst_ohm_pf1_exp)
        self.model.cnst_ohm_pf2 = pyo.Constraint(self.model.E, rule=cnst_ohm_pf2_exp)
        self.model.cnst_ohm_qf1 = pyo.Constraint(self.model.E, rule=cnst_ohm_qf1_exp)
        self.model.cnst_ohm_qf2 = pyo.Constraint(self.model.E, rule=cnst_ohm_qf2_exp)

        # ====================
        # III.e Power Balance
        # ====================
        self.model.sets_balance = pyo.BuildAction(rule=define_sets_balance_exp)
        self.model.cnst_p_balance = pyo.Constraint(self.model.B, rule=cnst_p_balance_exp)
        self.model.cnst_q_balance = pyo.Constraint(self.model.B, rule=cnst_q_balance_exp)

        # ====================
        # III.f Voltage Angle Difference
        # ====================
        self.model.cnst_vad_lower = pyo.Constraint(self.model.E, rule=cnst_vad_lower_exp)
        self.model.cnst_vad_upper = pyo.Constraint(self.model.E, rule=cnst_vad_upper_exp)

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
        shunts = network['shunt']

        busidxs = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadidxs = sorted(list(loads.keys()))
        shuntidxs = sorted(list(shunts.keys()))

        branchidxs_all = sorted(list(branches.keys()))
        branchidxs = [branch_idx for branch_idx in branchidxs_all if branches[branch_idx]['br_status']>0]
        genidxs_all = sorted(list(gens.keys())) # it contains not active generators
        genidxs = [gen_idx for gen_idx in genidxs_all if gens[gen_idx]['gen_status']>0]

        ncost = 3 # all PGLib input files have three cost coefficients
        
        gen_per_bus = { busidx: [] for busidx in busidxs }
        load_per_bus = { busidx: [] for busidx in busidxs }
        branch_in_per_bus = { busidx: [] for busidx in busidxs }
        branch_out_per_bus = { busidx: [] for busidx in busidxs }
        shunt_per_bus = { busidx: [] for busidx in busidxs }

        
        # Generator
        pgmax, pgmin, qgmax, qgmin = {}, {}, {}, {}
        pginit, qginit = {}, {}
        cost = {}
        for gen_idx in genidxs:
            gen = gens[gen_idx]
            pgmax[gen_idx] = gen['pmax']
            pgmin[gen_idx] = gen['pmin']
            qgmax[gen_idx] = gen['qmax']
            qgmin[gen_idx] = gen['qmin']
            pginit[gen_idx] = gen['pg']
            qginit[gen_idx] = gen['qg']
            cost_raw = gen['cost']
            for i in range(ncost):
                cost[(gen_idx,i)] = cost_raw[i]
            gen_per_bus[gen['gen_bus']].append(gen_idx)
        
        # Load
        pd, qd = {}, {}
        for load_idx in loadidxs:
            load = loads[load_idx]
            pd[load_idx] = load['pd']
            qd[load_idx] = load['qd']
            load_per_bus[load['load_bus']].append(load_idx)

        # Shunt
        gs, bs = {}, {}
        for shunt_idx in shuntidxs:
            shunt = shunts[shunt_idx]
            gs[shunt_idx] = shunt['gs']
            bs[shunt_idx] = shunt['bs']
            shunt_per_bus[shunt['shunt_bus']].append(shunt_idx)

        # Bus
        vmmax, vmmin = {}, {}
        slack = []
        for bus_idx in busidxs:
            bus = buses[bus_idx]
            vmmax[bus_idx] = bus['vmax']
            vmmin[bus_idx] = bus['vmin']
            bustype = bus['bus_type']
            if bustype == 3:
                slack.append(bus_idx)
        
        # Branch
        rate_a = {}
        f_bus, t_bus = {}, {}
        g1, g2, b1, b2, T_R, T_I, T_m, g, b = {}, {}, {}, {}, {}, {}, {}, {}, {}
        angmin, angmax = {}, {}
        for branch_idx in branchidxs:
            branch = branches[branch_idx]
            rate_a_val = branch['rate_a']
            if rate_a_val == 0.: rate_a_val + 1e12
            rate_a[branch_idx] = rate_a_val
            f_bus[branch_idx] = branch['f_bus']
            t_bus[branch_idx] = branch['t_bus']
            g1[branch_idx] = branch['g_fr']
            g2[branch_idx] = branch['g_to']
            b1[branch_idx] = branch['b_fr']
            b2[branch_idx] = branch['b_to']
            T_m_val = branch['tap']
            shift = branch['shift']
            T_R[branch_idx] = T_m_val * math.cos(shift)
            T_I[branch_idx] = T_m_val * math.sin(shift)
            T_m[branch_idx] = T_m_val
            r = branch['br_r']
            x = branch['br_x']
            g[branch_idx] = r / (r**2 + x**2)
            b[branch_idx] = -x / (r**2 + x**2)
            angmin[branch_idx] = branch['angmin']
            angmax[branch_idx] = branch['angmax']
            branch_out_per_bus[branch['f_bus']].append(branch_idx) # from buses
            branch_in_per_bus[branch['t_bus']].append(branch_idx)

        if init_var is not None:
            pginit = init_var['pg']
            qginit = init_var['qg']
            vminit = init_var['vm']
            vainit = init_var['va']
            pf1init = init_var['pf1']
            pf2init = init_var['pf2']
            qf1init = init_var['qf1']
            qf2init = init_var['qf2']
        else:
            vminit = { idx: 1. for idx in busidxs }
            vainit = { idx: 0. for idx in busidxs }
            pf1init = { idx: 0. for idx in branchidxs }
            pf2init = { idx: 0. for idx in branchidxs }
            qf1init = { idx: 0. for idx in branchidxs }
            qf2init = { idx: 0. for idx in branchidxs }
                
        data = {
            'G': {None: genidxs},
            'B': {None: busidxs},
            'E': {None: branchidxs},
            'L': {None: loadidxs},
            'S': {None: shuntidxs},
            'pginit': pginit,
            'qginit': qginit,
            'vminit': vminit,
            'vainit': vainit,
            'pf1init': pf1init,
            'pf2init': pf2init,
            'qf1init': qf1init,
            'qf2init': qf2init,
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
            'f_bus': f_bus,
            't_bus': t_bus,
            'g1': g1, 'g2': g2, 'b1': b1, 'b2': b2,
            'T_R': T_R, 'T_I': T_I, 'T_m': T_m, 'g':g, 'b':b,
            'angmin': angmin, 'angmax': angmax
        }

        self.model.gen_per_bus_raw = gen_per_bus
        self.model.load_per_bus_raw = load_per_bus
        self.model.branch_in_per_bus_raw = branch_in_per_bus
        self.model.branch_out_per_bus_raw = branch_out_per_bus
        self.model.shunt_per_bus_raw = shunt_per_bus
        
        instance = self.model.create_instance({None: data}) # create instance (ConcreteModel), 
        # note that self.model is not duplicated because it is desired to be AbstractModel 
        # for taking different types of problem instances consistently.

        print('end')
        return instance