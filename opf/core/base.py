import pyomo.environ as pyo
from abc import ABC, abstractmethod
from typing import Dict, Any, Union
import warnings


class OPFBaseModel(ABC):
    """ abstract class for defining the problem.
        Should inherit this when adding the power model.
    """
    def __init__(self, model_type:str):
        self.model_type = model_type
        self.model = pyo.AbstractModel()
        self.instance = None

    def is_constructed(self) -> bool:
        """ whether to have ConcreteModel
        """
        if isinstance(self.instance,pyo.ConcreteModel):
            return True
        else:
            return False

    @abstractmethod
    def _build_model(self) -> None: pass

    @abstractmethod
    def _instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel: pass

    @abstractmethod
    def _solve(self, optimizer:pyo.SolverFactory, solve_method:bool = None, tee:bool = False, extract_dual:bool = False) -> Dict[str,Any]: pass

    @abstractmethod
    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False) -> None: pass

    def solve(self, solver:Union[bool,pyo.SolverFactory] = 'ipopt', solver_option:Dict[str,Any] = {}, solve_method:bool = None, tee:bool = False, extract_dual:bool = False) -> Dict[str,Any]: 
        if not isinstance(self.instance,pyo.ConcreteModel):
            raise RuntimeError("instance has not included in the model class. Please execute model.instantiate(network) first to create it.")
        if isinstance(solver, str):
            optimizer = pyo.SolverFactory(solver.lower())
        elif isinstance(solver, type(pyo.SolverFactory)):
            optimizer = solver
        else:
            raise RuntimeError("solver should be string (such as ipopt or gurobi) or pyo.SolverFactory object.")

        for k,v in solver_option.items():
            optimizer.options[k] = v
        
        return self._solve(optimizer, solve_method, tee, extract_dual)


    def instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> None: 
        print('instantiate model...', end=' ', flush=True)
        if isinstance(self.instance,pyo.ConcreteModel):
            warnings.warn("instance is already created. instantiating again will destroy the previous instance", RuntimeWarning)

        self.instance = self._instantiate(network, init_var, verbose)
        self.append_suffix(self.instance)
        print('end', flush=True)


    def append_suffix(self, instance:pyo.ConcreteModel) -> None:
        """ Generate suffix to access the duals for constraints and bounds. 
        Note that the variable name 'dual', 'ipopt_zL_out', ipopt_zL_in', ... cannot be changed.
        This is specified in Pyomo to access the duals.

        Args:
            instance (pyo.ConcreteModel): ConcreteModel that already set up all except for suffix
        """
        instance.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) # define the dual assess point
        instance.ipopt_zL_out = pyo.Suffix(direction=pyo.Suffix.IMPORT)
        instance.ipopt_zU_out = pyo.Suffix(direction=pyo.Suffix.IMPORT)
        instance.ipopt_zL_in = pyo.Suffix(direction=pyo.Suffix.EXPORT)
        instance.ipopt_zU_in = pyo.Suffix(direction=pyo.Suffix.EXPORT)
        return None


class NormalOPFModel(OPFBaseModel):
    """Normal Optimal Power Flow class that encompasses AC-OPF, DC-OPF DC-OPF using PTDF matrix
    """
    def __init__(self, model_type:bool):
        super().__init__(model_type)

    def _solve(self, optimizer:pyo.SolverFactory, solve_method:bool = None, tee:bool = False, extract_dual:bool = False) -> Dict[str,Any]:
        opt_results = optimizer.solve(self.instance, tee=tee)

        results = {'termination_status': opt_results.solver.termination_condition, 
                   'time': opt_results.solver.time,
                   'obj_cost': pyo.value(self.instance.obj_cost),
                   'sol': {}
                   }

        if results['termination_status'] in ['optimal', 'locallyOptimal', 'globallyOptimal']:
            self._write_output(results, extract_dual)
        
        return results
        
    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False) -> None:
        # extract primal solutions
        primal_sol = {}
        for v in self.instance.component_objects(pyo.Var, active=True):
            primal_sol_var = primal_sol.get(str(v), {})
            for idx in v:
                primal_sol_var[str(idx)] = v[idx].value
            primal_sol[str(v)] = primal_sol_var
        results['sol']['primal'] = primal_sol

        if extract_dual: # extract dual solutions
            # extract dual for constraints
            dual_sol = {}
            for c in self.instance.component_objects(pyo.Constraint, active=True):
                dual_sol_var = dual_sol.get(str(c), {})
                for idx in c:
                    dual_sol_var[str(idx)] = self.instance.dual[c[idx]]
                dual_sol[str(c)] = dual_sol_var
            results['sol']['dual'] = dual_sol

            # extract dual for bounds
            bound_sol = {}
            for v in self.instance.component_objects(pyo.Var, active=True):
                bound_sol_var = bound_sol.get(str(v), {})
                for idx in v:
                    if v[idx].lower is not None:
                        bound_sol_var["lb_"+str(idx)] = self.instance.ipopt_zL_out[v[idx]]
                    if v[idx].upper is not None:
                        bound_sol_var["ub_"+str(idx)] = self.instance.ipopt_zU_out[v[idx]]
                bound_sol[str(v)] = bound_sol_var  
            results['sol']['bound'] = bound_sol
        
        return None


    def setup_warmstart(self, warmstart_dict:Dict[str,Any]) -> None:
        if not self.is_constructed():
            raise RuntimeError("instance for warmstarting should be constructed before.")

        if 'primal' in warmstart_dict.keys(): # setup primal warmstart points
            primal_ws_dict = warmstart_dict['primal']
            for v in self.instance.component_objects(pyo.Var, active=True):
                if str(v) in primal_ws_dict:
                    for i in v:
                        v[i].value = primal_ws_dict[str(v)][str(i)]
        
        if 'dual' in warmstart_dict.keys(): # setup dual warmstart points
            dual_ws_dict = warmstart_dict['dual']
            for c in self.instance.component_objects(pyo.Constraint, active=True):
                if str(c) in dual_ws_dict:
                    for i in c:
                        self.instance.dual.set_value(c[i], dual_ws_dict[str(c)][str(i)])

        if 'bound' in warmstart_dict.keys(): # setup dual for bound constraint
            bound_ws_dict = warmstart_dict['bound']
            for v in self.instance.component_objects(pyo.Var, active=True):
                if str(v) in bound_ws_dict:
                    for i in v:
                        if "lb_"+str(i) in bound_ws_dict[str(v)]:
                            self.instance.ipopt_zL_in.set_value(v[i], bound_ws_dict[str(v)]["lb_"+str(i)])
                        if "ub_"+str(i) in bound_ws_dict[str(v)]:
                            self.instance.ipopt_zU_in.set_value(v[i], bound_ws_dict[str(v)]["ub_"+str(i)])

        return None