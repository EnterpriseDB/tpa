# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    REMAINDER=()
    while [[ $# -gt 0 ]]; do
        opt=$1
        shift

        case "$opt" in
            *)
                REMAINDER+=("$opt")
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    target=${1:?no switchover target specified}
    shift

    time playbook commands/switchover.yml -e target="$target" "$@"
}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec switchover clustername newprimary

Takes the name of an instance and performs an orderly switchover that
promotes the given instance to be the new primary and makes the other
instances (including the old primary) follow it.
HELP
}
