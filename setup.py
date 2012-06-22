#!/usr/bin/env python
from setuptools import setup, find_packages

import warehouse


install_requires = [
    "logan",
    "south",
    "django-model-utils>=1.1",
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
    zip_safe=False,

    entry_points={
        "console_scripts": [
            "warehouse = warehouse.utils.runner:main",
        ],
    },
)
