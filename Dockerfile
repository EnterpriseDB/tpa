# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

# Build this container image like this
#
#  docker build -t tpaexec:$(git describe --tags) -t tpaexec:latest .

# Use the container image, create an like this
#
#   alias tpaexec="docker run --rm -v $PWD:/work -v $HOME/.git:/root/.git -v $HOME/.gitconfig:/root/.gitconfig \
#      -v /var/run/docker.sock:/var/run/docker.sock \
#      -e USER_ID=$(id -u) -e GROUP_ID=$(id -g) tpaexec"
#
# Then run commands like this
#
#   tpaexec configure cluster -a M1 --postgresql 15 --failover-manager patroni --platform docker
#   tpaexec deploy cluster

FROM debian:latest

LABEL maintainer="EDB <tpa@enterprisedb.com>"

# Set up repositories and install packages, including the Docker CE CLI
# (https://docs.docker.com/engine/install/debian/).

RUN apt-get -y update && \
    apt-get -y install curl gnupg apt-transport-https \
      python3 python3-pip python3-venv openvpn patch git && \
    curl -fsSL https://download.docker.com/linux/debian/gpg >/etc/apt//trusted.gpg.d/docker.asc && \
    codename=$(awk -F= '/VERSION_CODENAME/{print $2}' /etc/os-release) && \
    arch=$(dpkg --print-architecture) && \
    echo "deb [arch=$arch] https://download.docker.com/linux/debian $codename stable" \
      >/etc/apt/sources.list.d/docker.list && \
    apt-get -y update && \
    apt-get -y install docker-ce-cli && \
    rm -rf /var/cache/apt/

# Copy tpaexec sources from the current directory into the image, and
# run `tpaexec setup` to complete the installation, and then `tpaexec
# selftest` to verify it.

ENV TPA_DIR=/opt/EDB/TPA

COPY . ${TPA_DIR}

RUN ln -sf ${TPA_DIR}/bin/tpaexec /usr/local/bin && \
    mkdir /opt/2ndQuadrant/ && \
    ln -sf ${TPA_DIR} /opt/2ndQuadrant/TPA && \
    tpaexec setup --use-community-ansible && \
    tpaexec selftest

WORKDIR /work
CMD ["--help"]
ENTRYPOINT ["/opt/EDB/TPA/entrypoint.sh"]
