#!/bin/bash

set -e

if [ "${FS_SCANNER}" = "blackduck" ]; then
    case "${FS_SCANNER_STAGE}" in
    "pre")
        echo "Setup for BlackDuck pre stage"
        # install ansible requirements for community use case only
        pip install -r requirements.txt -r requirements-ansible-8.txt
        export DETECT_PIP_REQUIREMENTS_PATH="requirements.txt, requirements-ansible-8.txt" >> $GITHUB_ENV
        ;;
    "post")
        echo "Nothing to do for BlackDuck post stage"
        ;;
    *)
        echo "Stage not found"
        exit 1
        ;;
    esac
fi
