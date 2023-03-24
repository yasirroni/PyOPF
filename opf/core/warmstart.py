import pyomo.environ as pyo
from typing import Any, Dict

def setup_warmstart(instance:pyo.ConcreteModel, warmstart_dict:Dict[str,Any]) -> None:
    if not instance.is_constructed():
        raise RuntimeError("instance for warmstarting should be ConcreteModel.")

    if 'primal' in warmstart_dict.keys(): # setup primal warmstart points
        primal_ws_dict = warmstart_dict['primal']
        for v in instance.component_objects(pyo.Var, active=True):
            if str(v) in primal_ws_dict:
                for i in v:
                    v[i].value = primal_ws_dict[str(v)][str(i)]
    
    if 'dual' in warmstart_dict.keys(): # setup dual warmstart points
        dual_ws_dict = warmstart_dict['dual']
        for c in instance.component_objects(pyo.Constraint, active=True):
            if str(c) in dual_ws_dict:
                for i in c:
                    instance.dual.set_value(c[i], dual_ws_dict[str(c)][str(i)])

    if 'bound' in warmstart_dict.keys(): # setup dual for bound constraint
        bound_ws_dict = warmstart_dict['bound']
        for v in instance.component_objects(pyo.Var, active=True):
            if str(v) in bound_ws_dict:
                for i in v:
                    if "lb_"+str(i) in bound_ws_dict[str(v)]:
                        instance.ipopt_zL_in.set_value(v[i], bound_ws_dict[str(v)]["lb_"+str(i)])
                    if "ub_"+str(i) in bound_ws_dict[str(v)]:
                        instance.ipopt_zU_in.set_value(v[i], bound_ws_dict[str(v)]["ub_"+str(i)])

    return None