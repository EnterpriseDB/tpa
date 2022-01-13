# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    args=()

    username=${1:?No username specified}
    shift

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
    file="$dir"/"$username"_password.yml
    if [[ ! -f $file && -f "$dir/$username".yml ]]; then
        file="$dir"/"$username".yml
    fi

    "$ansible"-vaultpw "${args[@]}" show "$file" "$@"
}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec show-password clustername username

Shows the password stored in the local inventory for the given user.
HELP
}
