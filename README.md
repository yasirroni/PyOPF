![GitHub](https://img.shields.io/github/license/seonho-park/PyOPF?label=license)
[![codecov](https://codecov.io/gh/seonho-park/PyOPF/branch/main/graph/badge.svg?token=QZTV5P31IC)](https://codecov.io/gh/seonho-park/PyOPF)
[![DOI](https://zenodo.org/badge/614393450.svg)](https://zenodo.org/badge/latestdoi/614393450)


# :zap: PyOPF: Optimal Power Flow Modeling in Python
`PyOPF` is Optimal Power Flow (OPF) modeling framework in Python. 
This modeling is basically based on [`Pyomo`](https://github.com/Pyomo/pyomo), which is a solver-agnostic optimization modeling package in Python. 
`PyOPF` generally can take [PGLib](https://github.com/power-grid-lib/pglib-opf) based input and formulate various OPF problems including AC-OPF, DC-OPF.


## Installation
```
pip install opf
```


* Dependencies
    + python>=3.8
    + pyomo>=6.5.0
    + numpy>=1.22.3
    + ipopt>=1.0.3


## Formulations
1. :o: AC-OPF (AC Optimal Power Flow): 
    ```python
    model = opf.build_model('acopf')
    ```
    - AC-OPF with a polar bus voltage variable representations.
    - The detailed formulation can be found in [PGLib](https://github.com/power-grid-lib/pglib-opf).
    - `PyOPF` takes the the input files from PGLib, which is basically based on MATPOWER format.
    - Uses various solvers supported in Pyomo including IPOPT and Gurobi to solve problem instances.

2. :o: DC-OPF (DC Optimal Power Flow)
    ```python
    model = opf.build_model('dcopf')      # base DC-OPF model
    model = opf.build_model('dcopf-ptdf') # DC-OPF model using PTDF
    ```
    - Linear approximation to AC-OPF.
    - Also support PTDF (power transfer distribution factor) based formulation.
    - Only use active power generations and bus voltage angles (for base DC-OPF) as variables.
    - Like AC-OPF, PGLib m-files can be taken as input.

## Warmstarting
* `PyOPF` fully supports primal and dual warmstarting for IPOPT. Documentation is to be added.
    ```python
    model.setup_warmstart(warmstart_solution_dict) 
    ```


## Examples
### Running AC-OPF from [PGLib](https://github.com/power-grid-lib/pglib-opf).
- Before solving the AC-OPF, you should install ***IPOPT***, which is a canonical solver for AC-OPF, as follows:
    ```
    conda install -c conda-forge ipopt
    ```

- Running the following AC-OPF problem
    ```python
    import opf

    # build abstract model for AC-OPF
    model = opf.build_model('acopf')

    # load pglib input model file
    network = opf.parse_file("./data/pglib_opf_case5_pjm.m")

    # create the model instance (concrete model)
    model.instantiate(network)

    # solve the problem
    result = model.solve(solver_option={'print_level' : 5, 'linear_solver': 'ma27'}, tee=True)

    # check the optimal objective value
    print('obj value', result['obj_cost'])

    # check the (primal) optimal solution
    print('primal solution', result['sol']['primal'])
    ```


## Citation
- If you exploit this repository in your research, please cite using the following BibTeX:

```
@software{
    PyOPF_2023,
    author = {Park, Seonho},
    doi = {10.5281/zenodo.7772531},
    license = {MIT},
    month = {10},
    title = {{PyOPF: Optimal Power Flow Modeling in Python}},
    version = {0.3.1},
    year = {2023}
}
```