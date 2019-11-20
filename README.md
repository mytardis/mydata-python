# mydata-python

[![Travis CI](https://travis-ci.org/jameswettenhall/mydata-python.svg?branch=master)](https://travis-ci.org/jameswettenhall/mydata-python) [![codecov](https://codecov.io/gh/jameswettenhall/mydata-python/branch/master/graph/badge.svg)](https://codecov.io/gh/jameswettenhall/mydata-python) [![Python 3](https://pyup.io/repos/github/jameswettenhall/mydata-python/python-3-shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/) [![Updates](https://pyup.io/repos/github/jameswettenhall/mydata-python/shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/)


A Python library for managing data uploads to MyTardis

mydata-python is MyData without wxPython.

It can be used as a Python library for:

 * A command-line interface
 * A Python GUI
 * Exposing Python functionality via ZeroRPC (ZeroMQ) which can be used by a Javascript GUI

## Example usage:

Find the appropriate location for the `MyData.cfg` settings file, and read its settings into
the SETTINGS singleton object:

```
>>> from mydata.conf import settings
>>> settings.general.instrument_name
'Test Instrument1'
```

## Stability

Whilst MyData (wxPython) is a relatively mature application, the
`mydata-python` library is in the early stages of being refactored out of
MyData, so it should not be considered stable - Nov 2019.

## Tests

Tests can be run with

```
pytest --cov=mydata
```

or

```
pytest --cov=mydata --cov-report=html
```
