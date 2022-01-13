# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

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

    time (
        provision "$@" && deploy "$@" &&
        playbook commands/generate-images.yml "$@" &&
        deprovision "$@"
    )
}
