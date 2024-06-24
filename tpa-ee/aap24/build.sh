#! /bin/bash
usage=$(
    cat <<END
build.sh [options]

available options:

    --tag, -t TAG
        tag to use for the image, default to "tpa-ee:latest"

    --base-image -b {"rhel", "alpine"}
        image to use as base image, defaults to "RHEL"

    -v
        verbose output
END
)
while [[ $# -gt 0 ]]; do
    opt=$1
    case "$opt" in
    "--tag" | "-t")
        shift
        tag=$1
        shift
        ;;
    "--base-image" | "-b")
        shift
        base_image=$1
        shift
        ;;
    "-v")
        shift
        v=true
        ;;
    *)
        echo "Unknown parameter ${1} provided"
        echo "${usage}"
        exit 1
        ;;
    esac
done

tag=${tag:-"tpa-ee:latest"}
base_image=${base_image:-"rhel"}

if [[ $v ]]; then
    echo Initializing the build environment
fi
# enusre pip is available
python -m ensurepip
# verify that venv exists or generate it
python -m venv build-venv

if [[ $v ]]; then
    echo Activate the build env
fi

# shellcheck source=/dev/null
source build-venv/bin/activate

# activate and install deps
if [[ $v ]]; then
    echo Install build dependencies
fi
python -m pip install -r build-requirements.txt
if [[ $v ]]; then
    python --version
    ansible-builder --version
    ansible-navigator --version
fi
# build the image
if [[ $v ]]; then
    verbose=("--verbosity" "2")
fi
ansible-builder build \
    --file="${base_image}/execution-environment.yml" \
    --context="../../" \
    --container-runtime="docker" \
    --tag="${tag}" \
    --squash "new" \
    --no-cache \
    "${verbose[@]}"
# deactivate venv
deactivate
# clean venv
rm -rf build-venv/