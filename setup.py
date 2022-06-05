#!/usr/bin/env python
"""Setup for anthemav module."""
from setuptools import setup


def readme():
    """Return README file as a string."""
    with open("README.rst", "r") as f:
        return f.read()


setup(
    name="anthemav",
    version="1.4.0",
    author="David McNett",
    author_email="nugget@macnugget.org",
    url="https://github.com/nugget/python-anthemav",
    license="LICENSE",
    packages=["anthemav"],
    scripts=[],
    description="Python API for controlling Anthem Receivers",
    long_description=readme(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "anthemav_monitor = anthemav.tools:monitor",
        ]
    },
)
