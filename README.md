![GitHub](https://img.shields.io/github/license/seonho-park/PyOPF?label=license)


# :zap:PyOPF: Python-based Optimal Power Flow Modeling
Python based optimal power flow modeling framework. This modeling is basically based on [Pyomo](https://github.com/Pyomo/pyomo).
Pyomo is solver-agnostic optimization modeling package. This repo utilizes Pyomo for modeling various optimal power flow formulations in power system applications.

## Installation
```
pip install opf
```

* Dependencies
    + python>=3.9
    + pyomo==6.5.0
    + numpy>=1.22.3
    + ipopt>=1.0.3


## Formulations
1. :o: AC-OPF (AC Optimal Power Flow): 
    - The formulation can be found in [PGLib](https://github.com/power-grid-lib/pglib-opf).
    - **PyOPF** takes the the input files in PGLib, which is basically based on MATPOWER format.
    - Uses various solvers that are supported in Pyomo including IPOPT to solve the problem instance.

2. :x: DC-OPF (DC Optimal Power Flow)
    - Linear approximation to AC-OPF.
    - To be added

3. :x: SC-AC-OPF (Security Constrained AC Optimal Power Flow)
    -  To be added


## Getting started
### [Example] Running AC-OPF from [PGLib](https://github.com/power-grid-lib/pglib-opf).
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
