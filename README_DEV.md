# Development README

## Object Relationships

```plaintext
ABC
└── OPFBaseModel
    ├── NormalOPFModel
    │   ├── DCOPFModel
    │   ├── DCOPFModelPTDF
    │   ├── ACOPFModel
    │   └── UCACOPFModel
    └── SCOPFModel
```

## Build Model

The `opf.build_model(model_type)` is located at `opf.core.func.build_model(model_type)` and will call `model._build_model()`.

## Instantiate

The `model.instantiate(network)` is located at `NormalOPFModel.instantiate(network, init_var)`. It will call `.utils._preprocessing_network(network)` and `self._instantiate(network, init_var, verbose)`.
