#!/usr/bin/env python
from setuptools import setup, find_packages

import warehouse


install_requires = [
    "Django>=1.4",

    "django-appconf",
    "django-json-field",
    "django-model-utils>=1.1",
    "django-hstore",
    "django-tastypie",
    "logan",
    "south",

    "python_dateutil >= 1.5, < 2.0",
    "distutils2",
    "psycopg2",
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

    packages=find_packages(exclude=["tests"]),
    package_data={"": ["LICENSE"], "warehouse": ["templates/*.html"]},
    include_package_data=True,

    zip_safe=False,

    entry_points={
        "console_scripts": [
            "warehouse = warehouse.utils.runner:main",
        ],
    },
)
