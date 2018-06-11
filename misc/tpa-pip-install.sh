#!/bin/sh
#
# Checks if there is an activated virtualenv and installs the pip
# packages from files located in /opt/2ndQuadrant/TPA/pip-packages
# © Copyright 2ndQuadrant, 2018


# Are there any pips?
command -v pip
NO_PIP="$(echo $?)"
# Check whether we have pip
if [ "$NO_PIP" = "0" ] ; then
# Check whether we have an activated virtualenv
  WHERES_PIP=$(pip -V | tail -1 | grep "from /usr/lib/" | wc -l)
  if [ $WHERES_PIP = 0 ]; then
# Upgrade pip whilst we are here
    pip install --upgrade --no-cache-dir --no-index --find-links=file:/opt/2ndQuadrant/TPA/pip-packages pip>=10.0.1
    pip install --no-cache-dir --no-index --find-links=file:/opt/2ndQuadrant/TPA/pip-packages -r /opt/2ndQuadrant/TPA/python-requirements.txt
    pip install --no-cache-dir --no-index --find-links=file:/opt/2ndQuadrant/TPA/pip-packages -r /opt/2ndQuadrant/TPA/pip-packages/ansible/requirements.txt
    pip install --no-cache-dir file:/opt/2ndQuadrant/TPA/pip-packages/ansible/
  else
    echo "ERR-no-virt: could not find virtualenv"
    exit 1
  fi
else
  echo "ERR-no-pips: pip not found, virtualenv not found"
  exit 2
fi
exit 0
