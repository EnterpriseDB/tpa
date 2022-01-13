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

    instances=${1:?No instances specified}
    shift

    DESTROY=no
    if [ "${1:-'NO_PLEASE_SAVE_MY_CLUSTER'}" = "I_REALLY_WANT_TO_DESTROY_MY_ENTIRE_CLUSTER=yes" ]; then
        DESTROY=yes
        shift
    fi

    # We terminate the old instances after performing some sanity
    # checks, provision replacements for them, and deploy to the
    # newly-provisioned instances.

    playbook "$TPA_DIR/platforms/aws/terminate-for-rehydration.yml" \
        -e i_really_want_to_destroy_my_entire_cluster=$DESTROY \
        -e '{"my_hosts_lines": []}' --limit "$instances" "$@"

    provision_args=(-e "require_reattachment=yes")
    provision_args+=(-e "reattach_hosts=$instances")
    if [ -f prehydrate-vars.yml ]; then
        provision_args+=(-e @prehydrate-vars.yml)
    fi
    provision "${provision_args[@]}" "$@"
    deploy -e rehydrate=yes -e deploy_hosts="$instances" "$@"
}

_tpaexec_help() {
    cat <<HELP
Command: tpaexec rehydrate clustername instance1[,instance2,…]

Takes a comma-separated list of hostnames and "rehydrates" each host:

1. Ensures that all extra volumes attached to the instance are tagged
   correctly and set to not be deleted on termination of the instance.
2. Terminates the instances and waits for the operation to complete.
3. Provisions replacements for each terminated instance.
4. Redeploys software on the new instances.
HELP
}
