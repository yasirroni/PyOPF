from typing import Any, Dict, Union, List
import pyomo.environ as pyo

from .base import SCOPFModel
from .acopf_exp import pg_bound_exp, obj_cost_exp
from .dcopf_exp import cnst_power_bal_ptdf_exp, cnst_pf_ptdf_exp, pf_bound_exp
from .scdcopf_exp import *


class SCDCOPFModel(SCOPFModel):
    """Security Constrained DC OPF optimization formuation (extensive formuation)
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
        self.model.pd = pyo.Param(self.model.L, within=pyo.Reals, mutable=True)
        self.model.rate_a = pyo.Param(self.model.E, within=pyo.NonNegativeReals, mutable=True)
        self.model.cost = pyo.Param(self.model.G, self.model.ncost, within=pyo.Reals, mutable=True)
        self.model.load_injection = pyo.Param(self.model.E, within=pyo.Reals, mutable=True)
        self.model.gamma = pyo.Param(self.model.G, within=pyo.Reals, mutable=True)

        # # ====================
        # # II.    Variables
        # # ====================
        self.model.pg = pyo.Var(self.model.G, initialize=self.model.pg_init, bounds=pg_bound_exp, within=pyo.Reals) # active generation (injection), continuous
        self.model.pg_kg = pyo.Var(self.model.G, self.model.K_g, bounds = pg_kg_bound_exp, within=pyo.Reals) # active generation when generator contingency occurs
        self.model.pg_ke = pyo.Var(self.model.G, self.model.K_e, bounds = pg_ke_bound_exp, within=pyo.Reals) # active generation when line contingency occurs
        self.model.x_kg = pyo.Var(self.model.G, self.model.K_g, within=pyo.Binary) # disjunction representing the primary response model when generator contingency occurs
        self.model.x_ke = pyo.Var(self.model.G, self.model.K_e, within=pyo.Binary) # disjunction representing the primary response model when generator contingency occurs
        self.model.n_kg = pyo.Var(self.model.K_g, bounds = (0.,1.), within=pyo.Reals) # global extent of generation increase when generator contingency occurs
        self.model.n_ke = pyo.Var(self.model.K_e, bounds = (0.,1.), within=pyo.Reals) # global extent of generation increase when line contingency occurs
        
        self.model.pf = pyo.Var(self.model.E, bounds=pf_bound_exp, within=pyo.Reals) # power flow for base case # it is neccesary for defining power flow for line contingency

        # ====================
        # III.   Constraints
        # ====================

        # ====================
        # III.a Define Base Case Power Flow 
        # ====================
        self.model.cnst_pf = pyo.Constraint(self.model.E, rule=cnst_pf_repr_exp) # base case power flow # define using PTDF

        # ====================
        # III.b Power Flow Contingency
        # ====================
        self.model.cnst_pf_kg = pyo.Constraint(self.model.E, self.model.K_g, rule=cnst_pf_kg_exp) # generator contingency
        self.model.cnst_pf_ke = pyo.Constraint(self.model.E, self.model.K_e, rule=cnst_pf_ke_exp) # line contingency

        # ====================
        # III.c Primary Response for Generator Contingency
        # ====================
        self.model.cnst_pg_kg = pyo.Constraint(self.model.K_g, rule=cnst_pg_kg_exp) 
        self.model.cnst_pr_kg1 = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_pr_kg1_exp)
        self.model.cnst_pr_kg2 = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_pr_kg2_exp)
        self.model.cnst_pr_kg3 = pyo.Constraint(self.model.G, self.model.K_g, rule=cnst_pr_kg3_exp)

        # ====================
        # III.d Primary Response for Line Contingency
        # ====================
        self.model.cnst_pr_ke1 = pyo.Constraint(self.model.G, self.model.K_e, rule=cnst_pr_ke1_exp)
        self.model.cnst_pr_ke2 = pyo.Constraint(self.model.G, self.model.K_e, rule=cnst_pr_ke2_exp)
        self.model.cnst_pr_ke3 = pyo.Constraint(self.model.G, self.model.K_e, rule=cnst_pr_ke3_exp)

        # ====================
        # IIII.   Objective
        # ====================
        self.model.obj_cost = pyo.Objective(sense=pyo.minimize, rule=obj_cost_exp)


        return None


    def _instantiate(self, network:Dict[str,Any], 
                          init_var:Dict[str,Any] = None, 
                          generator_contingency:Union[str,List[str]] = 'all',
                          line_contingency:Union[str,List[str]] = 'all',
                          verbose:bool = False,
                          **kwargs) -> pyo.ConcreteModel: 
        return None
        

    def _solve(self, optimizer:pyo.SolverFactory, solve_method:bool = None, tee:bool = False, extract_dual:bool = False) -> Dict[str,Any]: pass

    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False) -> None: pass