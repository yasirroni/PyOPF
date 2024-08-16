# Contributing

## Environment

```shell
python3.12 -m venv env
source env/bin/activate
```

## Install

```shell
pip install -e .
pip install requirements.txt
pip install pytest-cov
```

## Test

```shell
python -m pytest -s -v --cov=./tests --cov-report=xml
```
