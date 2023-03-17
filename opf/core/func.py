from .acopf import AbstractACOPFModel
from .dcopf import AbstractDCOPFModel
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
    elif model_type == 'dcopf':
        model = AbstractDCOPFModel(model_type)
    else:
        assert False

    model._build_model()
    return model