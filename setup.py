#!/usr/bin/env python
import sys

from setuptools import setup, find_packages

install_requires = [
    "Flask",
    "Flask-Script",
    "Flask-SQLAlchemy",

    "distutils2",
]

if sys.version_info < (2, 7):
    install_requires += [
        "importlib",
    ]

setup(
    name="warehouse",
    version="0.1.dev1",

    description="API Driven Python Package Index",
    long_description=open("README.rst").read(),
    url="https://github.com/crateio/warehouse/",
    license=open("LICENSE").read(),

    author="Donald Stufft",
    author_email="donald.stufft@gmail.com",

    install_requires=install_requires,

    packages=find_packages(exclude=["tests"]),
    zip_safe=False,

    entry_points={
        "console_scripts": [
            "warehouse = warehouse.commands.__main__:main",
        ],
    },
)
