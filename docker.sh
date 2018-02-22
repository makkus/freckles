#! /usr/bin/env bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$THIS_DIR"

docker build -t "freckles/freckles" .
docker run -it --mount type=bind,source="$THIS_DIR",target="/root/freckles/freckles"  freckles/freckles /bin/bash
