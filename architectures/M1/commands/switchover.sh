set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename $0)
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
                REMAINDER+=($opt)
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    target=${1:?no switchover target specified}
    shift

    playbook switchover.yml -e target=$target "$@"
}
