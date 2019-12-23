# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='sipgateio-oauth-python',
    version='0.1.0',
    description='A demonstration on how to authenticate against the sipgate REST API using the OAuth mechanism.',
    long_description=readme,
    author='sipgate.io Team',
    author_email='io-team@sipgate.de',
    url='https://github.com/sipgate-io/sipgateio-oauth-python/',
    license=license,
    packages=find_packages(exclude=())
)
