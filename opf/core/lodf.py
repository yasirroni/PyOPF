from typing import Dict, Any, Tuple, List
from scipy.sparse.linalg import spsolve
import numpy as np
import warnings

from .utils import compute_bus_susceptance_matrix, compute_line_incidence_matrix, compute_branch_susceptance_matrix, _preprocessing_network
 

def compute_lodf(network:Dict[str,Any], branch_outage_idxs:List[int]) ->  np.ndarray:
    """ compute line outage distribution factor (LODF) matrix for N-1 contingencies
    It assumes that we are monitoring all the branches while the outage occurs at one line (N-1 line contingency).
    
    LODF = PTDF_MO @ (I-PTDF_OO)^-1

    Ref: Guo, Jiachun, et al. "Direct calculation of line outage distribution factors." IEEE Transactions on Power Systems 24.3 (2009): 1633-1634.

    Args:
        network (Dict[str,Any]): pglib network
        branch_outage_idxs (List[int]): branch indices for the outage (contingency)

    Returns:
        np.ndarray: LODF matrix
    """
    _preprocessing_network(network)
    buses = network['bus']
    busids = sorted(list(buses.keys()))
    slack = [ buses[busid]['index'] for busid in busids if buses[busid]['bus_type'] == 3]
    if len(slack) != 1:
        raise ValueError(f'The number of slack buses should be 1. But it is now {len(slack)}.')
    slack = slack[0]

    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = np.asarray([branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0]) # factor out not working branches
    E = branchids.size

    noutage = len(branch_outage_idxs)
    branch_O = np.asarray(branch_outage_idxs)

    S_b = compute_bus_susceptance_matrix(network, slack) # BxB
    S_br = compute_branch_susceptance_matrix(network)
    PHI = compute_line_incidence_matrix(network).toarray() # BxE

    S_inv_PHI = spsolve(S_b,PHI)

    S_inv_PHI[slack, :] = 0
    PTDF = S_br @ S_inv_PHI # ExE branch-to-branch PTDF

    PTDF_MO = PTDF[:,branch_O]
    PTDF_OO = PTDF_MO[branch_O, np.arange(noutage)]
    LODF = PTDF_MO * (1./(1.-PTDF_OO))
    LODF[branch_O, np.arange(noutage)] = -1.
    return LODF

def check_line_contingency(network:Dict[str,Any], line_contingency:List[str]) ->  List[str]:
    """ check if line contingency induces network isolation.
    """
    buses = network['bus']
    busids = sorted(list(buses.keys()))
    slack = [ buses[busid]['index'] for busid in busids if buses[busid]['bus_type'] == 3]
    if len(slack) != 1:
        raise ValueError(f'The number of slack buses should be 1. But it is now {len(slack)}.')
    slack = slack[0]

    branches = network['branch']
    branchids_all = sorted(list(branches.keys()))
    branchids = np.asarray([branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0]) # factor out not working branches
    E = branchids.size

    branch_O = np.asarray([branches[branchid]['index'] for branchid in line_contingency])
    noutage = len(line_contingency)

    S_b = compute_bus_susceptance_matrix(network, slack) # BxB
    S_br = compute_branch_susceptance_matrix(network)
    PHI = compute_line_incidence_matrix(network).toarray() # BxE

    S_inv_PHI = spsolve(S_b,PHI)

    S_inv_PHI[slack, :] = 0
    PTDF = S_br @ S_inv_PHI # branch-to-branch PTDF, ExE 

    PTDF_MO = PTDF[:,branch_O]
    PTDF_OO = PTDF_MO[branch_O, np.arange(noutage)]
    line_contingency_out = []
    for line_cont_, branchidx, PTDF_val in zip(line_contingency, branch_O, PTDF_OO):
        if np.isclose(PTDF_val, 1.):
            warnings.warn(f"Line contingency ID {line_cont_} is excluded because it causes network isolation.")
        else:
            line_contingency_out.append(line_cont_)

    return line_contingency_out
