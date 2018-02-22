FROM debian:stretch-slim

ARG FRECKLES_UID=1000


RUN apt-get -y update
RUN apt-get install -y curl bzip2 python-apt sudo

RUN useradd -u "${FRECKLES_UID}" -ms /bin/bash freckles && adduser freckles sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER freckles

# will be shadowed later on
COPY --chown=freckles:freckles . /home/freckles/freckles-src

# RUN  curl https://freckles.io | sudo bash -s -- frecklecute use-freckles-version /home/freckles/freckles-src
# or, to use conda:
RUN  curl https://freckles.io | bash -s -- frecklecute use-freckles-version /home/freckles/freckles-src

WORKDIR /home/freckles
