from .acopf import ACOPFModel
from .dcopf import DCOPFModel
from .dcopf_ptdf import DCOPFModelPTDF
from .base import OPFBaseModel


def build_model(model_type:str) -> OPFBaseModel:
    """ build optimal power flow model

    Args:
        model_type (str): optimal power flow model type 
                          acopf:      AC-OPF, 
                          dcopf:      DC-OPF, 
                          dcopf-ptdf: DC-OPF based on PTDF matrix

    Returns:
        OPFBaseModel: abstract power model
    """
    
    print('build model...', end=' ', flush=True)
    if model_type == 'acopf':
        model = ACOPFModel(model_type)
    elif model_type == 'dcopf':
        model = DCOPFModel(model_type)
    elif model_type == 'dcopf-ptdf':
        model = DCOPFModelPTDF(model_type) 
    else:
        assert False

    model._build_model()
    print('end', flush=True)
    return model