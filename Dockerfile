FROM debian:stretch-slim

# needed for freckelize to parse metadata, can be 'shadowed' with a volume when run

RUN apt-get -y update
RUN apt-get install -y curl bzip2 python-apt

COPY . /root/freckles/freckles

# RUN  curl https://freckles.io | bash -s -- frecklecute use-freckles-version /root/freckles/freckles
# or, to use conda:
RUN  curl https://freckles.io | FORCE_CONDA=true bash -s -- frecklecute use-freckles-version /root/freckles/freckles


