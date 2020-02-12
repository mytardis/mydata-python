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
  index    Index data which is already in its permanent location.
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

## Upload and Indexing Methods

The MyTardis API provides three ways to add a file to MyTardis:

* [Via multipart form POST](https://mytardis.readthedocs.io/en/master/dev/api.html#via-multipart-form-post)
* [Via staging location](https://mytardis.readthedocs.io/en/master/dev/api.html#via-staging-location)
* [Via shared permanent storage location](https://mytardis.readthedocs.io/en/master/dev/api.html#via-shared-permanent-storage-location)

### Upload Methods and Comparison with MyData GUI
 
The [MyData GUI](https://mydata.readthedocs.io/) supports the first two methods, but not the third.
The `mydata-python` library and Command-Line Interface support all three methods, but the third
method does not use the `MyData.cfg` settings file used by the MyData GUI.

The first two upload methods are available from the command-line interface, using the
`mydata upload` command.  The *Via staging location* upload method is preferred over the
*Via multipart form POST* method, because the multipart POST method can lead to high
server memory usage if large file uploads are permitted.  Just like uploading with the
MyData GUI, running `mydata upload` will automatically choose the best upload method,
depending on whether your MyData instance (identified by an Uploader UUID) has been
approved for uploads via staging.

The `mydata upload` command is intended to be usable as a drop-in replacement for the
MyData GUI, using the same `MyData.cfg` settings file, however some settings are not
supported.  For example scheduling settings are not supported, because a command-line
tool can be scheduled using third-party tools such as Cron.

If you don't already have a `MyData.cfg` file generated by the MyData GUI, you can
generate a fresh one using:

```
$ mydata config generate

MyTardis URL: http://mytardis.example.com
MyTardis Username: testuser1
MyTardis API key: api_key1
Facility Name: Test Facility
Instrument Name: Test Instrument
Data Directory: /path/to/data/
Contact Name: Joe Bloggs
Contact Email: Joe.Bloggs@example.com

Wrote settings to: /home/james/.local/share/MyData/MyData.cfg
```

### Indexing Already-Uploaded Files

The third way of adding a file to MyTardis - *Via shared permanent storage location* -
is available from the command-line interface, using the `mydata index` command.
This is intended to be used by advanced users who have already transferred the files
to the permanent storage location, e.g. using Rsync.

The `mydata index` command doesn't use the `MyData.cfg` file and it doesn't scan
folder structures (e.g. `Username / Dataset`).  Instead it is configured using
environment variables [which may be specified in a `.env` file](https://pypi.org/project/python-dotenv/)
and it expects that the user already has a MyTardis Experiment ID to add the dataset
folder(s) to.

An example `.env` file is included in the repository:

```
# dotenv.example: Copy to .env, and customize
# For now, this is only used for indexing ("mydata index ...")
MYTARDIS_USERNAME=username
MYTARDIS_API_KEY=apikey
MYTARDIS_URL=https://example.com
MYTARDIS_EXP_ID=123
MYTARDIS_STORAGE_BOX_NAME=my-archive-box1
MYTARDIS_STORAGE_BOX_PATH=/path/to/permanent/file/store/MY_ARCHIVE_BOX_1
MYTARDIS_SRC_PATH=/path/files/were/copied/from/
```

The dataset folder (or folders) to be indexed are provided as command-line argument(s), e.g.

```
$ mydata index /path/to/permanent/file/store/MY_ARCHIVE_BOX_1/dataset1

MYTARDIS_STORAGE_BOX_PATH: /path/to/permanent/file/store/MY_ARCHIVE_BOX_1/

Validated MyTardis settings.

Indexing folder: dataset1

Created Dataset record for 'dataset1' with ID: 12345

10 of 10 files have been indexed by MyTardis.
0 of 10 files have been verified by MyTardis.
10 of 10 files were newly indexed in this session.
```

In this example, we assume that a
[MyTardis Storage Box](https://mytardis.readthedocs.io/en/master/admin/storage.html)
record has been created with a name of `my-archive-box1` which includes a `location`
StorageBoxOption with value `/path/to/permanent/file/store/MY_ARCHIVE_BOX_1/`.
We also assume that a MyTardis experment exists with `id=123` and that the
MyTardis user identified by the `(username, apikey)` credentials has access to
that experiment via an [ObjectACL](https://mytardis.readthedocs.io/en/master/pydoc/tardis.tardis_portal.models.html#tardis.tardis_portal.models.access_control.ObjectACL) record.

The `MYTARDIS_SRC_PATH` can be used to calculate checksums to compare against
those of the files in `MYTARDIS_STORAGE_BOX_PATH`.  However, if the source path
is no longer accessible, then you can set `MYTARDIS_SRC_PATH` to be the same
as `MYTARDIS_STORAGE_BOX_PATH`, in which case `mydata index` will calculate
checksums in the permanent storage location.

If the permanent storage location is a Hierarchical Storage Management (HSM) system,
then it is best to ensure that all files are online before beginning the indexing,
rather than having the files recalled by `mydata index` as it calculates their checksums.

## Tests

Tests can be run with

```
pytest --cov=mydata
```

or

```
pytest --cov=mydata --cov-report=html
```
