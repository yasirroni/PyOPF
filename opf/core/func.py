from .acopf import AbstractACOPFModel
from .dcopf import AbstractDCOPFModel
from .dcopf_ptdf import AbstractDCOPFModelPTDF
from .base import AbstractPowerBaseModel


def build_model(model_type:str) -> AbstractPowerBaseModel:
    """ build optimal power flow model

    Args:
        model_type (str): optimal power flow model type 
                          acopf:      AC-OPF, 
                          dcopf:      DC-OPF, 
                          dcopf-ptdf: DC-OPF based on PTDF matrix

    Returns:
        AbstractPowerBaseModel: abstract power model
    """
    
    if model_type == 'acopf':
        model = AbstractACOPFModel(model_type)
    elif model_type == 'dcopf':
        model = AbstractDCOPFModel(model_type)
    elif model_type == 'dcopf-ptdf':
        model = AbstractDCOPFModelPTDF(model_type) 
    else:
        assert False

    model._build_model()
    return model