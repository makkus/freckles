#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.7',
    'nsbl==0.1.6'
]

test_requirements = [
    'pytest>=3.2.2'
]

setup(
    name='freckles',
    version='0.2.8',
    description="a dotfile manager, and more; quite cute",
    long_description=readme + '\n\n' + history,
    author="Markus Binsteiner",
    author_email='makkus@posteo.net',
    url='https://github.com/makkus/freckles',
    packages=[
        'freckles',
    ],
    package_dir={'freckles':
                 'freckles'},
    entry_points={
        'console_scripts': [
            'freckles=freckles.freckles_cli:cli',
            'freckelize=freckles.freckelize_cli:cli',
            'frecklecute=freckles.frecklecute_cli:cli',
            '_freckfreckfreck=freckles.freckles_dev_cli:cli'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='freckles',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7'
    ],
    test_suite='tests',
    tests_require=test_requirements
)
