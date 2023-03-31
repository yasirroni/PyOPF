from typing import Any, Dict, Union, List
import pyomo.environ as pyo
import numpy as np

from .base import SCOPFModel
from .acopf_exp import pg_bound_exp, obj_cost_exp
from .dcopf_exp import cnst_power_bal_ptdf_exp, cnst_pf_ptdf_exp, pf_bound_exp
from .scdcopf_exp import *
from .ptdf import compute_ptdf
from .lodf import compute_lodf, check_line_contingency

class SCDCOPFModelCCGA(SCOPFModel):
    """CCGA (Column-and-Constraint-Generation Algorithm) decomposition for Security Constrained DC OPF optimization formuation 
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
        self.model.K_g = pyo.Set() # whole generator indices for generator contingency 
        self.model.K_g_lazy = pyo.Set() # selected generator indices for generator contingency in consideration # used for defining complementarity constraints (primary response)

        # these two sets below are for flow limit constraints, which will be added lazily.
        self.model.E_K_g = pyo.Set(dimen=2) # to check flow limit for generator contingency in consideration
        self.model.E_K_e = pyo.Set(dimen=2) # to check flow limit for line contingency in consideration
        
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
        self.model.r_bar = pyo.Param(self.model.G, within=pyo.Reals, mutable=True) # primary response limit 

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous
        self.model.pg_kg = pyo.Var(self.model.G, self.model.K_g, bounds = pg_kg_bound_exp, within=pyo.Reals) # (provisional) active generation when generator contingency occurs
        
        self.model.n_kg = pyo.Var(self.model.K_g_lazy, bounds = (0.,1.), within=pyo.Reals) # global extent of generation increase when generator contingency occurs
        self.model.rho_kg = pyo.Var(self.model.G, self.model.K_g_lazy, bounds = (0.,None), within=pyo.Reals) # downward deviation of pg from linear response
        
        self.model.pf = pyo.Var(self.model.E, bounds=pf_bound_exp, within=pyo.Reals) # power flow for base case # it is neccesary to define power flow for line contingency

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Define Base Case Power Flow 
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_repr_exp) # base case power flow # defined using PTDF

        # ====================
        # III.b Power Flow Contingency (Lazy Constraints)
        # ====================
        self.model.cnst_pf_kg = pyo.Constraint(self.model.E_K_g, rule=cnst_pf_kg_lazy_exp) # generator contingency
        self.model.cnst_pf_ke = pyo.Constraint(self.model.E_K_e, rule=cnst_pf_ke_lazy_exp) # line contingency

        # ====================
        # III.c Power Balance
        # ====================
        self.model.cnst_power_bal = pyo.Constraint(rule=cnst_power_bal_ptdf_exp) # base case
        self.model.cnst_power_bal_kg = pyo.Constraint(self.model.K_g, rule=cnst_power_bal_ptdf_kg_exp) # generator contingency

        # ====================
        # III.d Provisional Post-Contingency Generation Limit
        # ====================
        self.model.cnst_provisional_kg = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_provisional_kg_exp)
        # ====================
        # III.e Primary Response for Generator Contingency
        # ====================
        self.model.cnst_pr_kg1 = pyo.Constraint(self.model.G, self.model.K_g_lazy, rule=cnst_pr_kg1_exp)
        self.model.cnst_pr_kg2 = pyo.Constraint(self.model.G, self.model.K_g_lazy, rule=cnst_pr_kg2_exp)

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
        self.beta1 = kwargs.get('beta1', 5.)
        self.beta2 = kwargs.get('beta2', 1.2)

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
            self.line_contingency = check_line_contingency(network, line_contingency) # exclude bridge lines if applicable
            outage_branchidxs = [branches[branchid]['index'] for branchid in self.line_contingency]
            lodf_raw = compute_lodf(network,outage_branchidxs)
            for e in branchids:
                i = branches[e]['index']
                for j, k in enumerate(self.line_contingency):
                    self.model.lodf[e,k] = lodf_raw[i,j]
        else:
            self.line_contingency = []
        
        # check generator contingencies
        # if generation capacity is zero, no need to consider the generator contingency for this generator
        self.generator_contingency = [genid for genid in generator_contingency if not np.isclose(pgcapa[genid],0.)]

        r_bar = {g: gamma[g]*pgcapa[g] for g in genids}


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
            'K_g': self.generator_contingency,
            'K_e': self.line_contingency,
            'r_bar': r_bar
        }

        instance = self.model.create_instance({None: data}, report_timing=verbose) # create instance (ConcreteModel)
        return instance

    def _solve(self, optimizer:pyo.SolverFactory, 
                     solve_method:bool = None, 
                     tee:bool = False, 
                     extract_dual:bool = False,
                     extract_contingency:bool = False) -> Dict[str,Any]:

        opt_results = optimizer.solve(self.instance, tee=tee) # initial solve
        
        self._binary_search()
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
            pg_ke_sol = {}

            for g in self.instance.G:
                for k in self.instance.K_g:
                    key = f"{g},{k}"
                    pg_kg_sol[key] = self.instance.pg_kg[g,k].value
            results['sol']['pg_kg'] = pg_kg_sol

            for g in self.instance.G:
                for k in self.instance.K_e:
                    key = f"{g},{k}"
                    pg_ke_sol[key] = self.instance.pg_ke[g,k].value
            results['sol']['pg_ke'] = pg_ke_sol

        return None

    def _binary_search(self):
        """ Binary search for retrieving generation post-contingency and some relavent
            Corresponding to Algorithm 1 in the paper 'An Exact and Scalable Problem Decomposition for
            Security-Constrained Optimal Power Flow'.
        """
        # obtain base case pg
        pd = np.asarray([self.instance.pd[id].value for id in self.instance.pd])
        pg = np.asarray([self.instance.pg[id].value for id in self.instance.pg])
        pgmax = np.asarray([self.instance.pg[id].bounds[1] for id in self.instance.pg])
        pgmin = np.asarray([self.instance.pg[id].bounds[0] for id in self.instance.pg])
        pgcapa = np.asarray([self.instance.pgcapa[id].value for id in self.instance.pg])
        
        branchids = [branchid for branchid in self.instance.E]
        genid2idx = {id:i for i, id in enumerate(self.instance.pg)}

        alpha_g = {} # maximum violation of thermal limit
        for genid in self.generator_contingency:
            print('contingency gen id', genid)
            gamma = self.instance.gamma[genid].value
            n_value, pg_k = self._binary_search_contingency(pd, pg, pgmin, pgmax, pgcapa, gamma, genid2idx, kid=genid)
            print('n_value', n_value)
            if n_value is None:
                raise RuntimeError(f"Binary search for post-contingency generation for generator contingency {genid} is failed.")
            alpha_g_ = self._compute_maximum_violation_thermal_limit_g(pg_k, pg)
            alpha_g[genid] = alpha_g_

        # alpha_e = {}
        # for branchid in self.line_contingency:
        #     gamma = self.instance.gamma[genid].value
        #     n_value, pg_k = self._binary_search_contingency(pd, pg, pgmin, pgmax, pgcapa, gamma, genid2idx, keid=branchid)
        #     # self._compute_maximum_violation_thermal_limit_e(alpha_e, pg_k)
        print('alpha_g!', alpha_g)
        exit()

    def _binary_search_contingency(self, pd, pg, pgmin, pgmax, pgcapa, gamma, genid2idx, kid, maxiter=100, tol=1e-5):
        K = self.instance.K_g_lazy
        n_var = self.instance.n_kg

        n_value = n_var[kid].value if kid in K else 0.5
        n_low, n_upp = 0., 1.

        pd_sum = pd.sum()
        print("###############################################################")
        print(f"##################### KID:{kid} ##########################")
        print("###############################################################")
        print("pg", pg)

        n_value_opt = None
        for j in range(maxiter):
            pg_k = pg + n_value*gamma*pgcapa
            pg_k = np.where(pg_k>pgmax, pgmax, pg_k)
            pg_k[genid2idx[kid]] = 0. # contingency for generation
            e = pg_k.sum() - pd_sum
            print(j, n_value, e)
            if np.abs(e) < tol:
                n_value_opt = n_value
                break
            elif e>0:
                n_upp = n_value
            else:
                n_low = n_value
            n_value = (n_low+n_upp)/2.
            j += 1
        return n_value_opt, pg_k



            
    def _compute_maximum_violation_thermal_limit_g(self, pg_k, pg):
        print('pg', pg)
        print('pg_k', pg_k)
        alpha_g = {}

        for e in self.instance.E:
            ptdf = np.asarray(self.instance.ptdf_g[e])
            gen_injection = ptdf @ pg_k
            pf_val = gen_injection - self.instance.load_injection[e].value
            alpha_g[e] = max(0., abs(pf_val) - self.instance.rate_c[e].value)
            
            assert np.isclose(np.dot(ptdf,pg) - self.instance.load_injection[e].value, self.instance.pf[e].value)
            # TODO delete pg from argument

        print('alpha_g', alpha_g)
        return alpha_g
        # exit()
            # ptdf = np.asarray()
