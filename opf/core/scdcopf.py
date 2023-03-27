from typing import Any, Dict
import pyomo.environ as pyo

from .base import SCOPFModel


class SCDCOPFModel(SCOPFModel):
    """Security Constrained DC OPF optimization formuation (extensive formuation)
    """
    def __init__(self, model_type):
        super().__init__(model_type)

    def _build_model(self) -> None: 
        """ Define the (abstract) SC-DC-OPF optimization model. 
            This is enabled without having the specific parameter values.
        """
        return None


    def _instantiate(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel: pass

    def _solve(self, optimizer:pyo.SolverFactory, solve_method:bool = None, tee:bool = False, extract_dual:bool = False) -> Dict[str,Any]: pass

    def _write_output(self, results:Dict[str,Any], extract_dual:bool = False) -> None: pass