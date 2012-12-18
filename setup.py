#!/usr/bin/env python
from setuptools import setup, find_packages

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

    packages=find_packages(exclude=["tests"]),
    package_data={
        "": ["LICENSE"],
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

    zip_safe=False,
)
