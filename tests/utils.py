"""
tests/utils.py
"""
import sys

def unload_modules():
    """Unload modules - called at the end of a test
    """
    modules = [
        'mydata.logs',
        'mydata.models.dataset',
        'mydata.models.experiment',
        'mydata.models.group',
        'mydata.models.user',
        'mydata.models.facility',
        'mydata.models.instrument',
        'mydata.models.folder',
        'mydata.models.lookup',
        'mydata.models.upload',
        'mydata.models.settings',
        'mydata.settings',
        'mydata.tasks.folders',
        'mydata.tasks.uploads'
    ]
    for module in modules:
        if module in sys.modules:
            del sys.modules[module]


def subtract(str1, str2):
    """
    Subtract strings, e.g. "foobar" - "foo" = "bar"
    to isolate recently added logs from total log history.
    """
    if not str2:
        return str1
    return "".join(str1.rsplit(str2))
