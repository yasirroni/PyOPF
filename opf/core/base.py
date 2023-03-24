import pyomo.environ as pyo
from abc import ABC, abstractmethod
from typing import Dict, Any


class AbstractPowerBaseModel(ABC):
    """ abstract class for defining the problem.
        Should inherit this when adding the power model.
    """
    def __init__(self, model_type:str):
        self.model_type = model_type
        self.model = pyo.AbstractModel()

    @abstractmethod
    def _build_model(self) -> None: pass

    @abstractmethod
    def instantiate_model(self, network:Dict[str,Any], init_var:Dict[str,Any] = None, verbose:bool = False) -> pyo.ConcreteModel: pass

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

