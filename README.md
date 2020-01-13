# mydata-python

[![Travis CI](https://travis-ci.org/jameswettenhall/mydata-python.svg?branch=master)](https://travis-ci.org/jameswettenhall/mydata-python) [![codecov](https://codecov.io/gh/jameswettenhall/mydata-python/branch/master/graph/badge.svg)](https://codecov.io/gh/jameswettenhall/mydata-python) [![Python 3](https://pyup.io/repos/github/jameswettenhall/mydata-python/python-3-shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/) [![Updates](https://pyup.io/repos/github/jameswettenhall/mydata-python/shield.svg)](https://pyup.io/repos/github/jameswettenhall/mydata-python/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


A Python library and command-line interface for managing data uploads to MyTardis

mydata-python is MyData without wxPython.

It can be used as a Python library for:

 * A command-line interface
 * A Python GUI
 * Exposing Python functionality via ZeroRPC (ZeroMQ) which can be used by a Javascript GUI

## Example usage (Python library):

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

## Example usage (command-line interface):

```
$ mydata
Usage: mydata [OPTIONS] COMMAND [ARGS]...

  A command-line tool for uploading data to MyTardis, supporting the MyData
  configuration file format used by the MyData desktop application

Options:
  --help  Show this message and exit.

Commands:
  config   Query or update settings in MyData.cfg
  scan     Scan folders from structure described in MyData.cfg
  upload   Upload files from structure described in MyData.cfg
  version  Display version
```

```
$ mydata config 
Usage: mydata config [OPTIONS] COMMAND [ARGS]...

  Query or update settings in MyData.cfg

Options:
  --help  Show this message and exit.

Commands:
  discover  Display location of MyData.cfg
  get       Get value from MyData.cfg
  list      List keys in MyData.cfg
  set       Set value in MyData.cfg
```

```
$ mydata config discover
/Users/james/Library/Application Support/MyData/MyData.cfg
```

```
$ mydata config get instrument_name
James Test Microscope
```

The "scan" command finds the dataset folders and looks up users (or groups) on
the MyTardis server, but doesn't actually upload any files.

```
$ mydata scan -v

Using MyData configuration in: /Users/james/Library/Application Support/MyData/MyData.cfg

Scanning /Users/Shared/GroupDatasetDemoData/ using the "User Group / Dataset" folder structure...

Found group folder: Group1 [GROUP "GroupPrefix-Group1" WAS NOT FOUND ON THE MYTARDIS SERVER]
Found group folder: Group2 [GROUP "GroupPrefix-Group2" WAS NOT FOUND ON THE MYTARDIS SERVER]

Found 7 dataset folders in /Users/Shared/GroupDatasetDemoData/
```

Only POST uploads are supported at present, and it is recommended to set a limit in your web
server configuration preventing large files from being uploaded via POST.  In the example
below, one file cannot be uploaded by POST because it is too large.  Additional upload methods
supporting large files will be added soon.

```
$ mydata upload -v

Using MyData configuration in: /Users/james/Library/Application Support/MyData/MyData.cfg

Scanning /Users/Shared/GroupDatasetDemoData/ using the "User Group / Dataset" folder structure...

Found group folder: Group1 [GROUP "GroupPrefix-Group1" WAS NOT FOUND ON THE MYTARDIS SERVER]
Found group folder: Group2 [GROUP "GroupPrefix-Group2" WAS NOT FOUND ON THE MYTARDIS SERVER]

Found 7 dataset folders in /Users/Shared/GroupDatasetDemoData/

71 of 72 files have been uploaded to MyTardis.
71 of 72 files have been verified by MyTardis.
0 of 72 files were newly uploaded in this session.
71 of 72 file lookups were found in the local cache.

Failed uploads:
02_BoneMarrow79999_62MB.jpg [Upload failed with HTTP 413 - Request Entity Too Large]
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
