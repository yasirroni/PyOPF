from typing import Dict, Any, Tuple
import numpy as np
from scipy.sparse.linalg import spsolve

from .utils import (compute_branch_susceptance_matrix,
                    compute_bus_susceptance_matrix,
                    compute_generator_incidence_matrix,
                    compute_load_incidence_matrix,
                    _preprocessing_network)


def compute_ptdf(network:Dict[str,Any]) ->  Tuple[Dict[str,Any], Dict[str,Any]]:
    _preprocessing_network(network)
    buses = network['bus']
    busids = sorted(list(buses.keys()))
    slack = [ buses[busid]['index'] for busid in busids if buses[busid]['bus_type'] == 3]
    if len(slack) != 1:
        raise ValueError(f'The number of slack buses should be 1. But it is now {len(slack)}.')
    slack = slack[0]

    S_br = compute_branch_susceptance_matrix(network) # ExB
    S_b = compute_bus_susceptance_matrix(network,slack) # BxB
    I_g = compute_generator_incidence_matrix(network) # BxG
    I_l = compute_load_incidence_matrix(network) # BxL
    
    return _compute_ptdf(S_br, S_b, I_g, I_l, slack)


def _compute_ptdf(S_br, S_b, I_g, I_l, slack, tol=1e-13):
    # # LDLT decomposition
    # Theoretically, LDLT should give better performance than LU decomposition for the symmetric matrix, but in reality, it performs worse.
    # This is because in Python, there is no canonical LDLT based linear system `solve` function.

    # L, D, perm = ldl(S_b, lower=True) 
    # L = L[perm,:]
    # D = np.diag(D)[perm]
    # D_inv = np.diag(1./D)

    # # solve for I_g
    # y_g = solve_triangular(L, I_g, lower=True)
    # y_g = D_inv @ y_g
    # x_g = solve_triangular(L.T, y_g, lower=False)

    # # solve for I_l
    # y_l = solve_triangular(L, I_l, lower=True)
    # y_l = D_inv @ y_l
    # x_l = solve_triangular(L.T, y_l, lower=False)

    x_g = spsolve(S_b, I_g).toarray()
    x_l = spsolve(S_b, I_l).toarray()
    x_g[slack,:] = 0.
    x_l[slack,:] = 0.

    # compute ptdf for gen and load
    ptdf_g = S_br @ x_g
    ptdf_l = S_br @ x_l

    ptdf_g = np.where(np.abs(ptdf_g)<=tol, 0., ptdf_g) # this is for facilitating Gurobi
    ptdf_l = np.where(np.abs(ptdf_l)<=tol, 0., ptdf_l)
    return ptdf_g, ptdf_l
