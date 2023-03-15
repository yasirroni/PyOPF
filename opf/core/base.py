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
    def instantiate_model(self, network:Dict[str,Any], init_var:Dict[str,Any] = None) -> pyo.ConcreteModel: pass

