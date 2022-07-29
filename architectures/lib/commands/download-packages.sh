#!/usr/bin/env bash
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

set -eu

if [[ "$0" == "${BASH_SOURCE[0]}" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    REMAINDER=()
    OPTS=()
    while [[ $# -gt 0 ]]; do
        opt=$1
        shift

        case "$opt" in
            --os)
                image_os=${1:?"docker image OS not specified"}
                shift
                ;;
            --os-version)
                os_version=${1:?"docker image OS version not specified"}
                shift
                ;;
            --docker-image)
                docker_image=${1:?"docker image not specified"}
                shift
                ;;
            --download-dir)
                download_dir=${1:?"path to download directory not provided"}
                shift
                OPTS+=('-e' "download_dir=$download_dir")
                ;;
            --exclude-packages)
                package_names=${1:?"package name not specified"}
                shift
                OPTS+=('-e' "exclude_packages_str=$package_names")
                ;;
            *)
                REMAINDER+=("$opt")
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    # $docker_image takes priority, if that's not set construct the image name from
    # image_os (lower case) and os_version (if set)
    docker_image="${docker_image:-${image_os:+tpa/${image_os,,}}${os_version:+:${os_version}}}"
    OPTS+=('-e' "default_docker_image=$docker_image")

    if [[ -z "${docker_image:+x}" ]]; then
        echo "Please specify an image for the package download container with --docker-image" >&2
        echo "(e.g., '--docker-image tpa/redhat', or tpa/debian, or tpa/ubuntu)" >&2
        exit 1
    fi

    time (
        playbook "${TPA_DIR}/architectures/lib/commands/download-packages.yml" \
          "${OPTS[@]}" \
          "$@"
    )
}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec download-packages clustername --docker-image tpa/<image>

Downloads all packages required by the cluster into a local-repo.

This command creates a temporary container to download packages (but
will not affect any existing cluster instances). You need a working
Docker setup to use it.

You must specify a Docker image (e.g., '--docker-image tpa/redhat') to
use for the temporary container used to download packages.

By default, downloaded packages are stored in a distribution-specific
subdirectory of your cluster's local-repo base directory,
e.g., local-repo/Debian/10 or local-repo/RedHat/8.

Use '--download-dir /path/to/base/directory' to use a base directory
other than $(pwd)/local-repo.

Use '--exclude-packages pkg1,pkg2,pkg3,…' to remove packages from the
list of packages to download.
HELP
}
