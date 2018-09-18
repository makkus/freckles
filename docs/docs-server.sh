#!/usr/bin/env bash

rm -fr build/html
sphinx-apidoc -f -o docs/source/ freckles
sphinx-autobuild -p 8001 docs build/html
