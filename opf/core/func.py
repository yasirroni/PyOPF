from .base import OPFBaseModel
from .acopf import ACOPFModel
from .dcopf import DCOPFModel
from .dcopf_ptdf import DCOPFModelPTDF
from .scdcopf import SCDCOPFModel
from .scdcopf_ccga import SCDCOPFModelCCGA

def build_model(model_type:str) -> OPFBaseModel:
    """ build optimal power flow model

    Args:
        model_type (str): optimal power flow model type 
                          acopf:        AC-OPF
                          dcopf:        DC-OPF 
                          dcopf-ptdf:   DC-OPF based on PTDF matrix
                          scdcopf:      SC-DC-OPF (extensive formulation)
                          scdcopf-ccga: SC-DC-OPF based on CCGA    

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
    elif model_type == 'scdcopf':
        model = SCDCOPFModel(model_type)
    elif model_type == 'scdcopf-ccga':
        model = SCDCOPFModelCCGA(model_type)
    else:
        assert False

    model._build_model()
    print('end', flush=True)
    return model