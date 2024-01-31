#!/bin/bash

set -e

if [ "${FS_SCANNER}" = "blackduck" ]; then
    case "${FS_SCANNER_STAGE}" in
    "pre")
        echo "Setup for BlackDuck pre stage"
        pip install -r requirements.txt
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
