#! /usr/bin/env bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$THIS_DIR"

if [[ "$1" == "--build" ]]; then
    docker build --no-cache -t "freckles/freckles" .
fi

docker run -it --mount type=bind,source="$THIS_DIR",target="/root/freckles/freckles"  freckles/freckles /bin/bash --login
