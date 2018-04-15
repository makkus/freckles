#!/usr/bin/env bash

sphinx-apidoc -f -o docs/source/ freckles
sphinx-autobuild -H 0.0.0.0 -p 8082 docs build/html
