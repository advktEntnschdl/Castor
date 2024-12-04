# Castor

A handy tool for performing parametric studies.

## installation

```bash
  cd <castor project directory>
  pip install .
```

## General usage

```bash
  castor <pythonConfigFile> <args>
```

## Examples

### Linear Elastic Tension Test in EdeleissFE

```bash
  cd examples/LinearElastic
  castor config.py --parallelJobs 10
```

