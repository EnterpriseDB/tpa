# Copyright © EnterpriseDB Corporation

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    instance=${1:?no instance specified}
    shift

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

    time playbook "$TPA_DIR/architectures/BDR-Always-ON/commands/pool-disable-server.yml" -e disable_instance="$instance" "$@"
}
