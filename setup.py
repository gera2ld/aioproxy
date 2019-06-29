#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = ['Click>=6.0', 'aiohttp>=3.4.4', 'gera2ld.pyserve']

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Gerald",
    author_email='i@gerald.top',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="A simple proxy server",
    entry_points={
        'console_scripts': [
            'aioproxy=aioproxy.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords='aioproxy',
    name='aioproxy',
    packages=find_packages(include=['aioproxy']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/gera2ld/aioproxy',
    version='0.1.0',
    zip_safe=False,
)
