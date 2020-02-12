#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup.py for mydata-python
"""
import io
import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRED = [
    "appdirs>=1.4",
    "click>=7.0",
    "netifaces>=0.10",
    "psutil>=5.6",
    "python-dateutil>=2.8",
    "python-dotenv>=0.11.0",
    "requests>=2.22",
    "requests-toolbelt>=0.9",
]

TEST_REQUIRED = [
    "coverage>=4.5",
    "paramiko>=2.6",
    "pytest>=5.2",
    "pytest-cov>=2.8",
    "pytest-env>=0.6",
    "requests-mock>=1.6",
]

# Load the package's __version__.py module as a dictionary.
ABOUT = {}
with io.open(os.path.join(HERE, "mydata", "__version__.py"), "r") as f:
    exec(f.read(), ABOUT)  # pylint: disable=exec-used

with io.open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    README = "\n" + f.read()

setup(
    name=ABOUT["__title__"],
    version=ABOUT["__version__"],
    description=ABOUT["__description__"],
    long_description=README,
    long_description_content_type="text/markdown",
    author=ABOUT["__author__"],
    author_email=ABOUT["__author_email__"],
    python_requires=">=3.5",
    url=ABOUT["__url__"],
    packages=find_packages(),
    install_requires=REQUIRED,
    extras_require={},
    include_package_data=True,
    license=ABOUT["__license__"],
    zip_safe=False,
    classifiers=[
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    cmdclass={},
    tests_require=TEST_REQUIRED,
    project_urls={"Source": "https://github.com/jameswettenhall/mydata-python"},
    entry_points={"console_scripts": ["mydata = mydata.client:run",],},
)
