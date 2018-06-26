#!/bin/sh
#
# Creates a virtualenv in /opt/2ndQuadrant/TPA/tpa-virtualenv
# and calls tpa-pip-install.sh to install the pip packages
# © Copyright 2ndQuadrant, 2018

# Check that we are root
if [ "$EUID" -ne 0 ]
  then echo "ERR-not-root: Please run as root" >&2
  exit 10
fi

# Is there enough space - would like 200M to be safe
SPACE=`df -m /opt/2ndQuadrant/TPA | tail -1 | awk '{ print $4 }'`
if [ "$SPACE" -lt "200" ] ; then
  echo "ERR-no-space: Need 200MB in /opt/2ndQuadrant/TPA" >&2
  exit 1
fi

# Check whether virtualenv command is present
if ! [ -x "$(command -v virtualenv)" ]; then
  echo "ERR-no-virtualenv: Install virtualenv!" >&2
  exit 2
fi

# Create virtualenv
virtualenv /opt/2ndQuadrant/TPA/tpa-virtualenv
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "ERR-create-virtualenv: Error creating /opt/2ndQuadrant/TPA/tpa-virtualenv" >&2
fi

# Activate it so that we can install pip modules
source /opt/2ndQuadrant/TPA/tpa-virtualenv/bin/activate
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "ERR-activate-virtualenv: Error activating virtualenv /opt/2ndQuadrant/TPA/tpa-virtualenv" >&2
fi

# Install the python dependencies into the virtualenv (including ansible)
/opt/2ndQuadrant/TPA/misc/tpa-pip-install.sh
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "ERR-pip-install: Error from /opt/2ndQuadrant/TPA/misc/tpa-pip-install.sh" >&2
fi
