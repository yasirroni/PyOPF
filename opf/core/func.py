from .acopf import AbstractACOPFModel
from .base import AbstractPowerBaseModel


def build_model(model_type:str) -> AbstractPowerBaseModel:
    """_summary_

    Args:
        model_type (str): acopf: AC-OPF

    Returns:
        AbstractPowerBaseModel: abstract power model
    """
    
    if model_type == 'acopf':
        model = AbstractACOPFModel(model_type)
        model._build_model()
    else:
        assert False

    return model