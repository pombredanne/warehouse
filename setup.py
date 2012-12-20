#!/usr/bin/env python
import sys

# Hack to prevent stupid error on exit of `python setup.py test`. (See
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html.)
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest

        sys.exit(pytest.main(self.test_args))


__about__ = {}

with open("warehouse/__about__.py") as fp:
    exec(fp, None, __about__)

setup(
    name=__about__["__title__"],
    version=__about__["__version__"],

    description=__about__["__summary__"],
    long_description=open("README.rst").read(),
    url=__about__["__uri__"],
    license=__about__["__license__"],

    author=__about__["__author__"],
    author_email=__about__["__email__"],

    install_requires=[
        "Flask",
        "Flask-SQLAlchemy",
        "Flask-Script",
        "boto",
        "eventlet",
        "progress",
        "psycopg2",
        "python-s3file>=1.1",
        "requests",
        "schema",
        "xmlrpc2",
    ],
    extras_require={
        "tests": [
            "pylint",
            "pytest",
            "pytest-pep8",
            "pytest-cov",
        ],
    },
    tests_require=[
        "pytest",
        "pytest-pep8",
        "pytest-cov",
    ],

    packages=find_packages(exclude=["tests"]),
    package_data={
        "warehouse": [
            "simple/templates/*.html",
            "synchronize/*.crt",
        ],
    },
    include_package_data=True,

    entry_points={
        "console_scripts": [
            "warehouse = warehouse.__main__:main",
        ],
    },

    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],

    cmdclass={"test": PyTest},
    zip_safe=False,
)
