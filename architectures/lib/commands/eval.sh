# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    expr=${1:?no expression specified}
    shift

    REMAINDER=()
    while [[ $# -gt 0 ]]; do
        opt=$1
        shift

        case "$opt" in
            --hosts)
                if [[ -z ${1:-''} ]]; then
                    error "$opt: No hosts specified"
                fi
                REMAINDER+=(-e "eval_hosts=$1")
                shift
                ;;

            --no-init)
                REMAINDER+=(-e "init=no")
                ;;

            *)
                REMAINDER+=("$opt")
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    time playbook "$TPA_DIR/architectures/lib/commands/eval.yml" -e expr="$expr" "$@"
}
