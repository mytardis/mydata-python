# mydata-python

[![Travis CI](https://travis-ci.org/jameswettenhall/mydata-python.svg?branch=master)](https://travis-ci.org/jameswettenhall/mydata-python) [![codecov](https://codecov.io/gh/jameswettenhall/mydata-python/branch/master/graph/badge.svg)](https://codecov.io/gh/jameswettenhall/mydata-python) [![Python 3](https://pyup.io/repos/github/jameswettenhall/mydata-python/python-3-shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/) [![Updates](https://pyup.io/repos/github/jameswettenhall/mydata-python/shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


A Python library for managing data uploads to MyTardis

mydata-python is MyData without wxPython.

It can be used as a Python library for:

 * A command-line interface
 * A Python GUI
 * Exposing Python functionality via ZeroRPC (ZeroMQ) which can be used by a Javascript GUI

## Example usage:

Find the appropriate location for the `MyData.cfg` settings file, and read some of its
settings:

```
>>> from mydata.conf import settings

>>> settings.config_path
'/Users/james/Library/Application Support/MyData/MyData.cfg'

>>> settings.instrument_name
'Test Instrument1'

>>> settings.folder_structure
'Experiment / Dataset'

>>> settings.data_directory
'tests/testdata/testdata-exp-dataset'
```

Scan folders:

```
from mydata.tasks.folders import scan_folders
from mydata.conf import settings

assert settings.folder_structure == 'Experiment / Dataset'

exps = []
folders = []

# We don't need callbacks for these in this case:
found_user = None
found_group = None

def found_exp(exp_folder_name):
    exps.append(exp_folder_name)

def found_dataset(folder):
    folders.append(folder)

scan_folders(found_user, found_group, found_exp, found_dataset)
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
