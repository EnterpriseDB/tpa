# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

# Build this container image like this
#
#  docker build -t tpaexec:$(git describe --tags) -t tpaexec:latest .

# To use the container image, create a shell alias like this
#
#   alias tpaexec="docker run --rm -v $PWD:/work -v $HOME/.git:/root/.git -v $HOME/.gitconfig:/root/.gitconfig \
#      -v /var/run/docker.sock:/var/run/docker.sock \
#      -e USER_ID=$(id -u) -e GROUP_ID=$(id -g) tpaexec"
#
# Then run commands like this
#
#   tpaexec configure cluster -a M1 --postgresql 15 --failover-manager patroni --platform docker
#   tpaexec deploy cluster

FROM debian:bookworm-slim

LABEL maintainer="EDB <tpa@enterprisedb.com>"

# Copy tpaexec sources from the current directory into the image
ENV TPA_DIR=/opt/EDB/TPA

COPY . ${TPA_DIR}

# Set up repositories and install packages, including the Docker CE CLI
# (https://docs.docker.com/engine/install/debian/).

RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
      curl gnupg apt-transport-https \
      python3 python3-pip python3-venv \
      openvpn patch git && \
    curl -fsSL https://download.docker.com/linux/debian/gpg >/etc/apt/trusted.gpg.d/docker.asc && \
    codename=$(awk -F= '/VERSION_CODENAME/{print $2}' /etc/os-release) && \
    arch=$(dpkg --print-architecture) && \
    echo "deb [arch=$arch] https://download.docker.com/linux/debian $codename stable" \
      >/etc/apt/sources.list.d/docker.list && \
    apt-get -y update && \
    apt-get -y install --no-install-recommends docker-ce-cli && \
    \
    # run `tpaexec setup` to complete the installation, and then `tpaexec selftest` to verify it. \
    \
    ln -sf ${TPA_DIR}/bin/tpaexec /usr/local/bin && \
    mkdir /opt/2ndQuadrant/ && \
    ln -sf ${TPA_DIR} /opt/2ndQuadrant/TPA && \
    tpaexec setup --use-community-ansible && \
    tpaexec selftest && \
    (cd "${TPA_DIR}" && git describe --tags >VERSION) && \
    \
    # Clean up unnecessary files and packages \
    \
    rm -rf ${TPA_DIR}/.[a-z]* && \
    apt purge -y python3-pip python3-venv build-essential && \
    apt autoremove -y && \
    apt autoclean -y && \
    apt clean -y && \
    rm -rf /var/cache/apt /var/lib/apt/lists

WORKDIR /work
CMD ["--help"]
ENTRYPOINT ["/opt/EDB/TPA/entrypoint.sh"]
