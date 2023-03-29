from typing import Dict, Any, Tuple, List
from scipy.sparse.linalg import spsolve
import numpy as np

from .utils import compute_bus_susceptance_matrix, compute_line_incidence_matrix, compute_branch_susceptance_matrix


# def compute_lodf(network:Dict[str,Any], branch_outage_idxs:List[int]) ->  np.ndarray:
    # """ compute line outage distribution factor (LODF) matrix for N-1 contingencies
    # It assumes that we are monitoring all the branches while the outage occurs at one line (N-1 line contingency).
    
    # LODF = PTDF_MO @ (I-PTDF_OO)^-1

    # Ref: Guo, Jiachun, et al. "Direct calculation of line outage distribution factors." IEEE Transactions on Power Systems 24.3 (2009): 1633-1634.

    # Args:
    #     network (Dict[str,Any]): pglib network
    #     branch_outage_idxs (List[int]): branch indices for the outage (contingency)

    # Returns:
    #     np.ndarray: LODF matrix
    # """
    
    # buses = network['bus']
    # busids = sorted(list(buses.keys()))
    # slack = [ buses[busid]['index'] for busid in busids if buses[busid]['bus_type'] == 3]
    # if len(slack) != 1:
    #     raise ValueError(f'The number of slack buses should be 1. But the size is now {len(slack)}.')
    # slack = slack[0]

    # branches = network['branch']
    # branchids_all = sorted(list(branches.keys()))
    # branchids = np.asarray([branch_id for branch_id in branchids_all if branches[branch_id]['br_status']>0]) # factor out not working branches

    # noutage = len(branch_outage_idxs)
    # branch_O = np.asarray(branch_outage_idxs)
    # branch_M = branchids # monitor all branches

    # S_b = compute_bus_susceptance_matrix(network,slack) # BxB
    # X = compute_reactance_vec(network)
    # PHI = compute_line2bus_incidence_matrix(network).toarray() # ExB
    # PSIs = PHI[branch_O, :]

    # # ptdf_oos = np.zeros(noutage)
    # # X_O = X[branch_O]
    # # for i, (PSI, X_O_) in enumerate(zip(PSIs,X_O)):
    # #     S_inv_PSI = spsolve(S_b,PSI)
    # #     X_o = X[branch_O[i]]
    # #     PTDF_MO = np.diag(1./X) * (PHI @ S_inv_PSI)
    # #     PTDF_OO = 1./X_O_ * (PSI @ S_inv_PSI)
    # #     ptdf_oos[i] = PTDF_OO

    # S_inv_PSI = spsolve(S_b,PSIs.T)
    # print('check', PHI.shape, S_inv_PSI.shape, (PHI @ S_inv_PSI).shape, (1./X).reshape(-1,1).shape)
    # PTDF_MO = (1./X).reshape(-1,1) * (PHI @ S_inv_PSI)
    # print('check', PTDF_MO.shape)
    # PTDF_OO = PTDF_MO[branch_O, np.arange(noutage)]
    # # print('check2', (1./(1.-PTDF_OO)).shape)
    # LODF = PTDF_MO * (1./(1.-PTDF_OO))
    # return LODF
    

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
    PTDF = S_br @ S_inv_PHI

    PTDF_MO = PTDF[:,branch_O]
    PTDF_OO = PTDF_MO[branch_O, np.arange(noutage)]
    LODF = PTDF_MO * (1./(1.-PTDF_OO))
    LODF[branch_O, np.arange(noutage)] = -1.

    return LODF

