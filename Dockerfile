# Copyright © EnterpriseDB Corporation

FROM debian:buster

MAINTAINER 2ndQuadrant <info@2ndQuadrant.com>

# TPA_DIR points to the path that will host tpaexec source code
# inside the image that we build.

ENV TPA_DIR=/root/tpaexec

# First, you must install some required system packages. (These would have
# been installed automatically as dependencies if you were installing the
# tpaexec package except git.)

RUN apt-get update && apt-get -y install python3.7 python3-pip python3-venv pwgen openvpn patch git

RUN mkdir ${TPA_DIR}

# Copy tpaexec sources inside the image

COPY . ${TPA_DIR}

# Invoke `tpaexec setup` so that it takes care of the basic tpaexec setup. By default,
# `tpaexec setup` will use the builtin Python 3 `-m venv` to create a venv under
# `$TPA_DIR/tpa-venv`, and activate it automatically whenever `tpaexec` is invoked.

RUN ${TPA_DIR}/bin/tpaexec setup

# Finally, test that everything is as it should be:
RUN ${TPA_DIR}/bin/tpaexec selftest

# Setup user env so that `tpaexec` is in user's default path everytime they log into
# the container

RUN echo "export PATH=$PATH:${TPA_DIR}/bin" > ~/.bashrc
ENV PATH="${TPA_DIR}/bin:${PATH}"

# Finally, test that everything is as it should be after `tpaexec` is invoked from
# default path:

RUN tpaexec selftest
