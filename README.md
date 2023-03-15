will add badges

# PyOPF: Python-based Optimal Power Flow Modeling
Python based optimal power flow modeling framework. This modeling is basically based on [Pyomo](https://github.com/Pyomo/pyomo) for modeling.
Pyomo is solver-agnostic optimization modeling package. This repo utilizes Pyomo for modeling optimal power flow formulations in power system applications.

## Quick Start
PyOPF requires Python 3.10+ and is highly recommended to run on **Linux** or **OSX** environment.

### Dependencies

- pyomo 6.5.0
- numpy 1.22.3
- ipopt 1.0.3

### Installation
```
pip install opf
```

## Getting started
### [Example] Running AC-OPF from [PGLib](https://github.com/power-grid-lib/pglib-opf).

```python
import opf

# build abstract model
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
