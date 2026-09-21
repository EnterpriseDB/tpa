#!/bin/bash

set -eu

if [ "${FS_SCANNER}" = "blackduck" ]; then
    case "${FS_SCANNER_STAGE}" in
    "pre")
        echo "Setup for BlackDuck pre stage"
        # Upgrade setuptools so BlackDuck's PIP detector doesn't flag the
        # old version Ubuntu ships (pip alone won't do this: it manages
        # its own version, not setuptools')
        pip install --upgrade pip setuptools
        # install ansible requirements for community use case only
        pip install -r requirements.txt
        echo DETECT_PIP_REQUIREMENTS_PATH="./source/requirements.txt" >> $GITHUB_ENV
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
if [[ "${FS_SCANNER}" = "sonarqube" ]]; then
    case "${FS_SCANNER_STAGE}" in
        "pre")

        # Stop script on any error
        set -e

        echo "--- Installing Python 3.12 ---"
        # 1. Add the deadsnakes PPA for newer Python versions on Ubuntu
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt-get update

        # 2. Install Python 3.12 and required dev tools
        sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

        # 3. Set Python 3.12 as the default 'python3' and 'python'
        # Priority 1 for existing versions, Priority 2 for 3.12 ensures it wins
        sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 2

        # 4. Install pip for Python 3.12
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

        # 5. Verify versions
        echo "Python version: $(python --version)"
        echo "Pip version: $(pip --version)"

        # 6. Upgrade setuptools so it doesn't get flagged as an old,
        # vulnerable component (pip alone won't do this: it manages its
        # own version, not setuptools')
        pip install --upgrade pip setuptools

        # 7. Install Tox
        pip install tox

        # 8. Run the specific Tox environment
        echo "--- Running Tox py312-test ---"
        tox -e py312-test
            ;;
        "post")
            echo "Nothing to do for SQ post stage"
            ;;
        *)
            echo "Stage not found"
            exit 1
    esac
fi
