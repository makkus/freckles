#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive

set -x
set -e

# if [ -d "/pip" ]; then
#    rm -f .pip
#    ln -s /pip "$HOME/.pip"
# fi

# create freckles virtualenv
BASE_DIR="$HOME/.local/opt"
FRECKLES_DIR="$BASE_DIR/freckles"
FRECKLES_VIRTUALENV_BASE="$FRECKLES_DIR/venv/"
FRECKLES_VIRTUALENV="$FRECKLES_VIRTUALENV_BASE/freckles"
FRECKLES_VIRTUALENV_ACTIVATE="$FRECKLES_VIRTUALENV/bin/activate"
export WORKON_HOME="$FRECKLES_VIRTUALENV"

sudo apt-get update || sudo apt-get update
sudo apt-get install -y build-essential git python-dev python-virtualenv libssl-dev libffi-dev stow libsqlite3-dev

mkdir -p "$FRECKLES_VIRTUALENV"
cd "$FRECKLES_VIRTUALENV_BASE"
virtualenv freckles

# install freckles & requirements
source freckles/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel


echo source "$FRECKLES_VIRTUALENV_ACTIVATE" >> "$HOME/.bashrc"

# install freckles
source "$FRECKLES_VIRTUALENV_ACTIVATE"
cd /freckles
pip install -r requirements_dev.txt
python setup.py develop
if [ -d "/nsbl" ]; then
    pip install -e "/nsbl"
fi
if [ -d "/frkl" ]; then
    pip install -e "/frkl"
fi
