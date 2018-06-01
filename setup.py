#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "Click>=6.7",
    "click-log>=0.1.8",
    "click-completion==0.2.1",
    "cookiecutter==1.6.0",
    "frkl>=0.1.0",
    "lucify>=0.1.0",
    "cursor>=1.2.0",
    "six>=1.11.0",
]

test_requirements = [
    'pytest>=3.2.2'
]

setup(
    name='freckles',
    version='0.5.4',
    description="DevOps your laptop!",
    long_description=readme + '\n\n' + history,
    author="Markus Binsteiner",
    author_email='makkus@frkl.io',
    url='https://github.com/makkus/freckles',
    packages=[
        'freckles',
    ],
    package_dir={'freckles':
                 'freckles'},
    entry_points={
        'console_scripts': [
            'freckles=freckles.freckles_cli:cli',
            'freckfreckfreck=freckles.freckles_dev_cli:cli'
        ],
        "freckles.tasklists": [
            "default=freckles:FrecklesDefaultTasklist"
        ]
    },
    scripts=[
        'freckles/external/scripts/inaugurate/inaugurate',
        'freckles/external/scripts/frankentree/frankentree',
        'freckles/external/scripts/frocker/frocker'
    ],
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='freckles ansible provisioning',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration'
    ],
    test_suite='tests',
    tests_require=test_requirements
)
