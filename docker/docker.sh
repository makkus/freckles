#! /usr/bin/env bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$THIS_DIR/.."

if [[ "$1" == "--build" ]]; then
    docker build -t "freckles/freckles" -f docker/Dockerfile --build-arg FRECKLES_UID=1000 .
fi

docker run -it --mount type=bind,source="$THIS_DIR/..",target="/home/freckles/freckles-src"  freckles/freckles /bin/bash --login
