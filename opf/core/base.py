import pyomo.environ as pyo
from abc import ABC, abstractmethod
from typing import Dict, Any, Union, List
import warnings

from .utils import _preprocessing_network


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
    def _solve(self, optimizer:pyo.SolverFactory, 
                     solve_method:bool = None, 
                     tee:bool = False, 
                     extract_dual:bool = False,
                     extract_contingency:bool = False) -> Dict[str,Any]: pass


    def solve(self, solver:Union[bool,pyo.SolverFactory] = 'ipopt', 
                    solver_option:Dict[str,Any] = {}, 
                    solve_method:bool = None, 
                    tee:bool = False, 
                    extract_dual:bool = False, 
                    extract_contingency:bool = False) -> Dict[str,Any]: 
        if not isinstance(self.instance,pyo.ConcreteModel):
            raise RuntimeError("instance has not included in the model class. Please execute `model.instantiate(network)` first to create it.")
        if isinstance(solver, str):
            optimizer = pyo.SolverFactory(solver.lower())
        elif isinstance(solver, type(pyo.SolverFactory)):
            optimizer = solver
        else:
            raise RuntimeError("solver should be string (such as ipopt or gurobi) or `pyo.SolverFactory` object.")

        for k,v in solver_option.items():
            optimizer.options[k] = v
        
        return self._solve(optimizer, solve_method, tee, extract_dual, extract_contingency)

    @abstractmethod
    def instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> None: pass


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

    @abstractmethod
    def _instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel: pass

    def _solve(self, optimizer:pyo.SolverFactory, 
                     solve_method:bool = None, 
                     tee:bool = False, 
                     extract_dual:bool = False,
                     extract_contingency:bool = False) -> Dict[str,Any]:
        opt_results = optimizer.solve(self.instance, tee=tee)

        results = {'termination_status': str(opt_results.solver.termination_condition), 
                   'time': float(opt_results.solver.time),
                   'obj_cost': pyo.value(self.instance.obj_cost),
                   'sol': {}
                   }

        if results['termination_status'] in ['optimal', 'locallyOptimal', 'globallyOptimal']:
            self._write_output(results, extract_dual, extract_contingency)
        
        return results
        
    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False, extract_contingency:bool = False) -> None:
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

    def instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> None: 
        print('instantiate model...', end=' ', flush=True)
        if isinstance(self.instance,pyo.ConcreteModel):
            warnings.warn("instance is already created. instantiating again will destroy the previous instance", RuntimeWarning)

        _preprocessing_network(network)
        self.instance = self._instantiate(network, init_var, verbose)
        self.append_suffix(self.instance)
        print('end', flush=True)


class SCOPFModel(OPFBaseModel):
    """Security Constrained Optimal Power Flow base class
    """
    def __init__(self, model_type:bool):
        super().__init__(model_type)

    @abstractmethod
    def _instantiate(self, network:Dict[str,Any], 
                          init_var:Dict[str,Any] = None, 
                          generator_contingency:List[str] = [],
                          line_contingency:List[str] = [],
                          verbose:bool = False,
                          **kwargs) -> pyo.ConcreteModel: pass


    def instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> None: 
        return self.instantiate(network=network, init_var=init_var, generator_contingency='all', line_contingency='all', verbose=verbose)


    def instantiate(self, network:Dict[str,Any], 
                          init_var:Dict[str,Any] = None, 
                          generator_contingency:Union[str,List[str]] = 'all',
                          line_contingency:Union[str,List[str]] = 'all',
                          verbose:bool = False, **kwargs) -> None:
        print('instantiate model...', end=' ', flush=True)
        if isinstance(self.instance,pyo.ConcreteModel):
            warnings.warn("instance is already created. instantiating again will destroy the previous instance", RuntimeWarning)

        _preprocessing_network(network)

        if isinstance(generator_contingency,str):
            if generator_contingency.lower() != 'all':
                raise RuntimeError("The argument 'generator_contingency' should be 'all' or specifies the generator ID list")
            genids_all = sorted(list(network['gen'].keys())) 
            generator_contingency = [gen_id for gen_id in genids_all if network['gen'][gen_id]['gen_status']>0] # factor out not working generators
        elif isinstance(generator_contingency,list):
            # check sanity
            for genid in generator_contingency:
                if not genid in network['gen']:
                    raise RuntimeError(f"Generator ID {genid} in the argument 'generator_contingency' is not placed in the given network.")
        else:
            raise RuntimeError("The argument 'generator_contingency' should be 'all' or specifies the generator ID list")

    
        if isinstance(line_contingency,str):
            if line_contingency.lower() != 'all':
                raise RuntimeError("The argument 'line_contingency' should be 'all' or specify the transmission ID list")
            branchids_all = sorted(list(network['branch'].keys()))
            line_contingency = [branch_id for branch_id in branchids_all if network['branch'][branch_id]['br_status']>0] # factor out not working branches
        elif isinstance(line_contingency,list):
            # check sanity
            for lineid in line_contingency:
                if not lineid in network['branch']:
                    raise RuntimeError(f"Branch ID {lineid} in the argument 'line_contingency' is not placed in the given network.")
        else:
            raise RuntimeError("The argument 'line_contingency' should be 'all' or specify the transmission ID list")

        self.instance = self._instantiate(network, init_var, generator_contingency, line_contingency, verbose, **kwargs)
        # self.append_suffix(self.instance) # extracting dual or warmstarting dual is not supported
        print('end', flush=True)