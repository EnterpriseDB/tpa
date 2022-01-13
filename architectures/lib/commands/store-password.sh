# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    args=()
    while [[ $# -gt 0 ]]; do
        opt=$1
        shift

        case "$opt" in
            --secret-name)
                secret_name=${1:?secret name not specified}
                shift
                ;;
            --random)
                args+=(-c "$TPA_DIR"/architectures/lib/password)
                ;;
            --)
                break
                ;;
            *)
                REMAINDER+=("$opt")
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    if [[ ${secret_name:-''} == "" ]]; then
        username=${1:?No username specified}
        secret_name="$username"_password
        shift
    fi

    if [ -f vault/vault_pass.txt ]; then
        args+=(--vault-password-file vault/vault_pass.txt)
    fi

    dir=""
    if [[ -d ./inventory ]]; then
        dir=$(find ./inventory -path '*/group_vars/*/secrets' -type d)
    fi
    if [[ -z "$dir" ]]; then
        error "inventory directory does not exist (did you run tpaexec provision?)"
    fi
    file="$dir"/"$secret_name".yml

    "$ansible"-vaultpw "${args[@]}" store "$file" "$@"

}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec store-password clustername username [--random]

Stores an encrypted new password for the given user in the inventory.

Prompts you to enter a new password by default, but will generate and
use a random password instead if you specify --random.

Note: the new password is only stored in the local inventory. It will be
changed on the target instances (if needed) only during the next deploy.
HELP
}
