#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='iot-analytic',
    version='0.0.1',
    description='Distributed IoT Analytics :: GCP Dataflow',
    python_requires='>=3.5',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    namespace_packages=['analytic']
)
