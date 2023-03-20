![GitHub](https://img.shields.io/github/license/seonho-park/PyOPF?label=license)
[![codecov](https://codecov.io/gh/seonho-park/PyOPF/branch/main/graph/badge.svg?token=QZTV5P31IC)](https://codecov.io/gh/seonho-park/PyOPF)
[![DOI](https://zenodo.org/badge/614393450.svg)](https://zenodo.org/badge/latestdoi/614393450)


# :zap: PyOPF: Optimal Power Flow Modeling in Python
Python based optimal power flow modeling framework. This modeling is basically based on [Pyomo](https://github.com/Pyomo/pyomo).
Pyomo is a solver-agnostic optimization modeling package in Python. 
This repo utilizes Pyomo for modeling various optimal power flow formulations in power system applications.


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
    - AC-OPF with a polar bus voltage variables.
    - The detailed formulation can be found in [PGLib](https://github.com/power-grid-lib/pglib-opf).
    - **PyOPF** takes the the input files in PGLib, which is basically based on MATPOWER format.
    - Uses various solvers that are supported in Pyomo including IPOPT to solve the problem instance.

2. :o:DC-OPF (DC Optimal Power Flow)
    ```python
    model = opf.build_model('dcopf') # base DCOPF model
    ```
    - Linear approximation to AC-OPF.
    - Also support PTDF (power transfer distribution factor) based formulation.
    - Only use active power generations and bus voltage angles as variables.

3. :x:SC-DC-OPF (Security Constrained DC Optimal Power Flow)
    -  To be added


4. :x:SC-AC-OPF (Security Constrained AC Optimal Power Flow)
    -  To be added


## Warmstarting
* **PyOPF** supports primal and dual warmstarting. Documentation is to be added.
    ```python
    opf.setup_warmstart(instance, warmstart_dict) 
    ```


## Examples
### Running AC-OPF from [PGLib](https://github.com/power-grid-lib/pglib-opf).
- Before solving the AC-OPF, you should install ***IPOPT***, which is a canonical solver for AC-OPF, as follows:
    ```
    conda install -c conda-forge ipopt
    ```

- Running the following example AC-OPF problem
    ```python
    import opf

    # build abstract model for AC-OPF
    model = opf.build_model('acopf')

    # load pglib based model file
    network = opf.parse_file("./data/pglib_opf_case5_pjm.m")

    # create the concrete model
    instance = model.instantiate_model(network)

    # define the optimization solver
    solver = SolverFactory("ipopt")

    # solve the problem
    results = solver.solve(instance, options={'print_level' : 5, 'linear_solver': 'ma27'}, tee=True)

    # check the optimal objective value
    print('obj value', value(instance.obj_cost))

    # check the optimal solution
    for v in instance.component_objects(Var, active=True):
        print("Variable",v)  
        for index in v:
            print ("   ",index, value(v[index]))  
    ```


## Citation
- If you exploit this repository in your research, please cite using the following BibTeX:

```
@software{
    PyOPF_2023,
    author = {Park, Seonho},
    doi = {10.5281/zenodo.7738744},
    license = {MIT},
    month = {3},
    title = {{PyOPF: Optimal Power Flow Modeling in Python}},
    version = {0.1.0},
    year = {2023}
}
```