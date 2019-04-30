[![PyPI status](https://img.shields.io/pypi/status/freckles.svg)](https://pypi.python.org/pypi/freckles/)
[![PyPI version](https://img.shields.io/pypi/v/freckles.svg)](https://pypi.python.org/pypi/freckles/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/freckles.svg)](https://pypi.python.org/pypi/freckles/)
[![Pipeline status](https://gitlab.com/freckles-io/freckles/badges/develop/pipeline.svg)](https://gitlab.com/freckles-io/freckles/pipelines)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# freckles

*Elastic & composable scripting.*


## Description

Documentation still to be done.

# Development

Assuming you use [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) for development, here's how to setup a 'freckles' development environment manually:

    pyenv install 3.7.3
    pyenv virtualenv 3.7.3 freckles
    git clone https://gitlab.com/frkl/freckles
    cd <freckles_dir>
    pyenv local freckles
    pip install -e .[develop,testing,docs]
    pre-commit install


## Copyright & license

Please check the [LICENSE](/LICENSE) file in this repository (it's a short license!), also check out the [*freckles* license page](https://freckles.io/license) for more details.

[Parity Public License 6.0.0](https://licensezero.com/licenses/parity)

[Copyright (c) 2019 frkl OÜ](https://frkl.io)
