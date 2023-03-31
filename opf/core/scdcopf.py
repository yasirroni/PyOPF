from typing import Any, Dict, Union, List
import pyomo.environ as pyo
import numpy as np

from .base import SCOPFModel
from .acopf_exp import pg_bound_exp, obj_cost_exp
from .dcopf_exp import cnst_power_bal_ptdf_exp, cnst_pf_ptdf_exp, pf_bound_exp
from .scdcopf_exp import *
from .ptdf import compute_ptdf
from .lodf import compute_lodf, check_line_contingency

class SCDCOPFModel(SCOPFModel):
    """Security Constrained DC OPF optimization formuation (extensive formuation)
    Reference: 
      - Velloso, Alexandre, Pascal Van Hentenryck, and Emma S. Johnson. 
        "An exact and scalable problem decomposition for security-constrained optimal power flow." 
        Electric Power Systems Research 195 (2021): 106677.
      - Petra, Cosmin G., and Ignacio Aravena. 
        "Solving realistic security-constrained optimal power flow problems." 
        arXiv preprint arXiv:2110.01669 (2021).
    """

    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None: 
        """ Define the (abstract) SC-DC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        self.model.B = pyo.Set() # bus indices
        self.model.G = pyo.Set() # generator indices
        self.model.E = pyo.Set() # branch indices
        self.model.L = pyo.Set() # load indices
        self.model.slack = pyo.Set() # the slack buses
        self.model.ncost = pyo.Set() # the number of costs
        self.model.K_g = pyo.Set() # generator indices for generator contingency
        self.model.K_e = pyo.Set() # branch (line) indices for line contingency

        # # ====================
        # # I.    Parameters
        # # ====================
        self.model.pg_init = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmin = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgmax = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pgcapa = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)
        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.rate_c = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)
        self.model.load_injection = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.gamma = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous
        self.model.pg_kg = pyo.Var(self.model.G, self.model.K_g, bounds = pg_kg_bound_exp, within=pyo.Reals) # active generation when generator contingency occurs

        self.model.n_kg = pyo.Var(self.model.K_g, bounds = (0.,1.), within=pyo.Reals) # global extent of generation increase when generator contingency occurs        
        self.model.rho_kg = pyo.Var(self.model.G, self.model.K_g, bounds = (0.,None), within=pyo.Reals) # downward deviation of pg from linear response
        
        self.model.pf = pyo.Var(self.model.E, bounds=pf_bound_exp, within=pyo.Reals) # power flow for base case # it is neccesary to define power flow for line contingency

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Define Base Case Power Flow 
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_repr_exp) # base case power flow # defined using PTDF

        # ====================
        # III.b Power Flow Contingency
        # ====================
        self.model.cnst_pf_kg = pyo.Constraint(self.model.E, self.model.K_g, rule=cnst_pf_kg_exp) # generator contingency -- based on PTDF and primary response
        self.model.cnst_pf_ke = pyo.Constraint(self.model.E, self.model.K_e, rule=cnst_pf_ke_exp) # line contingency -- based on LODF

        # ====================
        # III.c Power Balance
        # ====================
        self.model.cnst_power_bal = pyo.Constraint(rule=cnst_power_bal_ptdf_exp) # base case
        self.model.cnst_power_bal_kg = pyo.Constraint(self.model.K_g, rule=cnst_power_bal_ptdf_kg_exp) # generator contingency
        
        # ====================
        # III.c Primary Response for Generator Contingency
        # ====================
        self.model.cnst_pr_kg1 = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_pr_kg1_exp)
        self.model.cnst_pr_kg2 = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_pr_kg2_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)

        return None


    def _instantiate(self, network:Dict[str,Any], 
                          init_var:Dict[str,Any] = None, 
                          generator_contingency:List[str] = [],
                          line_contingency:List[str] = [],
                          verbose:bool = False,
                          **kwargs) -> pyo.ConcreteModel: 

        gens = network['gen']
        buses = network['bus']
        branches = network['branch']
        loads = network['load']

        branchids = sorted(list(branches.keys()))
        genids = sorted(list(gens.keys())) 
        busids = sorted(list(buses.keys())) # sort this for consistency between the pyomo vector and the input matpower 
        loadids = sorted(list(loads.keys()))
        
        genidxs = [gens[genid]['index'] for genid in genids]

        # retrieve parameters 
        gamma = kwargs.get('gamma', 0.05) # 0.05 is the value used in the paper `An exact and scalable problem decomposition for security-constrained optimal power flow`
        if isinstance(gamma, float):
            gamma = {genid:gamma for genid in genids}
        self.model.eps = kwargs.get('eps', 1e-4) # Page 14 in the paper 'Solving realistic security-constrained optimal power flow problems'
        rate_c_increase_rate = kwargs.get('rate_c_increase_rate', 0.33)

        ncost = 3 # all PGLib input files have three cost coefficients

        # Generator
        pgmax, pgmin, pgcapa, pg, qg, cost = {}, {}, {}, {}, {}, {}
        for gen_id in genids:
            gen = gens[gen_id]
            pgmax[gen_id] = gen['pmax']
            pgmin[gen_id] = gen['pmin']
            pgcapa[gen_id] = max(0., gen['pmax'] - gen['pmin'])
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
        rate_c = {}
        ang2pf = {}
        for branch_id in branchids:
            branch = branches[branch_id]
            rate_a_val = branch['rate_a']
            rate_c_val = branch['rate_c']
            if np.isclose(rate_a_val,0.): rate_a_val = 1e12
            rate_a[branch_id] = rate_a_val
            if np.isclose(rate_c_val,0.): rate_c_val = 1e12
            if np.isclose(rate_c_val,rate_a_val): rate_c_val = (1.+rate_c_increase_rate)*rate_a_val
            rate_c[branch_id] = rate_c_val
        
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
        

        self.model.lodf = {}
        # check network connectivity in line contingencies
        if len(line_contingency)>0:
            line_contingency = check_line_contingency(network, line_contingency) # exclude bridge lines if applicable
            outage_branchidxs = [branches[branchid]['index'] for branchid in line_contingency]
            lodf_raw = compute_lodf(network,outage_branchidxs)
            for e in branchids:
                i = branches[e]['index']
                for j, k in enumerate(line_contingency):
                    self.model.lodf[e,k] = lodf_raw[i,j] 
        
        # check generator contingencies
        # if generation capacity is zero, no need to consider the generator contingency for this generator
        generator_contingency = [genid for genid in generator_contingency if not np.isclose(pgcapa[genid],0.)]

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
            'pgcapa': pgcapa,
            'cost': cost,
            'rate_a': rate_a,
            'rate_c': rate_c,
            'load_injection': load_injection,
            'gamma': gamma,
            'K_g': generator_contingency,
            'K_e': line_contingency,
        }

        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel)
        return instance

    def _solve(self, optimizer:pyo.SolverFactory, 
                     solve_method:bool = None, 
                     tee:bool = False, 
                     extract_dual:bool = False,
                     extract_contingency:bool = False) -> Dict[str,Any]:
        opt_results = optimizer.solve(self.instance, tee=tee)

        results = {'termination_status': opt_results.solver.termination_condition, 
                   'time': opt_results.solver.time,
                   'obj_cost': pyo.value(self.instance.obj_cost),
                   'sol': {}
                   }

        if results['termination_status'] in ['optimal', 'locallyOptimal', 'globallyOptimal']:
            self._write_output(results, extract_dual, extract_contingency)
        
        return results

    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False, extract_contingency:bool = False) -> None:
        # extract active generation solutions
        pg_sol = {}
        for idx in self.instance.pg:
            pg_sol[str(idx)] = self.instance.pg[idx].value
        results['sol']['pg'] = pg_sol

        if extract_contingency:
            pg_kg_sol = {}
            for g in self.instance.G:
                for k in self.instance.K_g:
                    key = f"{g},{k}"
                    pg_kg_sol[key] = self.instance.pg_kg[g,k].value
            results['sol']['pg_kg'] = pg_kg_sol

        return None