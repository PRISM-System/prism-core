FROM axolotlai/axolotl:main-latest

ARG DEBIAN_FRONTEND=noninteractive
# apex, jupyter, jupyterlab ... are already installed in the container

RUN apt-get update && apt-get install -y --no-install-recommends \
            git \
            ssh \
            build-essential \
            locales \
            ca-certificates \
            curl \
            unzip \
            vim \
            wget \
            tmux \
            pciutils \
            gnome-keyring \
            htop \
            fonts-nanum \
            ## clean up 
            && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# encoding setup
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ARG UNAME1
ARG UID1
ARG GID
RUN groupadd -g $GID -o $UNAME1
RUN useradd -m -u $UID1 -g $GID -o -s /bin/bash $UNAME1
USER $UNAME1
WORKDIR /workspace