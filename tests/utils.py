"""
tests/utils.py
"""
import sys

def unload_modules():
    """Unload modules - called at the end of a test
    """
    modules = [
        'mydata.models.dataset',
        'mydata.models.experiment',
        'mydata.models.group',
        'mydata.models.user',
        'mydata.models.facility',
        'mydata.models.instrument',
        'mydata.models.folder',
        'mydata.models.upload',
        'mydata.models.settings',
        'mydata.settings',
        'mydata.tasks'
    ]
    for module in modules:
        if module in sys.modules:
            del sys.modules[module]
