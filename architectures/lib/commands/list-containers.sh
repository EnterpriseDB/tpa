# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

filter="label=Name=$(basename $PWD)"
format='table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Label "Cluster"}}\t{{.Status}}'

_tpaexec_command() {
    docker ps --format "$format" --filter "$filter" --all
}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec list-containers clustername

Shows a summary of docker containers provisioned for a cluster, whether
running or stopped.
HELP
}
