#!/usr/bin/env python
import os

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import warehouse


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        from configurations import importer

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
        os.environ.setdefault("DJANGO_CONFIGURATION", "Tests")

        importer.install()
        pytest.main(self.test_args)


install_requires = [
    "Django>=1.4",

    "django-appconf",
    "django-configurations",
    "django-haystack",
    "django-hstore",
    "django-json-field",
    "django-model-utils>=1.1",
    "django-tastypie",
    "django-uuidfield",
    "south",

    "python_dateutil>=2.1",
    "distutils2",
    "docutils",
    "progress",
    "psycopg2",
    "redis",
    "requests",
    "rq",
    "lxml",
]

setup(
    name="warehouse",
    version=warehouse.__version__,

    description="API Driven Python Package Index",
    long_description=open("README.rst").read(),
    url="https://github.com/crateio/warehouse/",
    license=open("LICENSE").read(),

    author="Donald Stufft",
    author_email="donald.stufft@gmail.com",

    install_requires=install_requires,
    tests_require=["pytest", "pytest-django"],

    packages=find_packages(exclude=["tests"]),
    package_data={"": ["LICENSE"], "warehouse": ["templates/*.html", "templates/search/indexes/warehouse/*.txt", "downloads/*.crt"]},
    include_package_data=True,

    zip_safe=False,

    entry_points={
        "console_scripts": [
            "warehouse = warehouse.__main__:main",
        ],
    },

    cmdclass = {"test": PyTest},
)
