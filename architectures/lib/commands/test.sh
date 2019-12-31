# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

set -eu

if [[ "$0" == "$BASH_SOURCE" ]]; then
    script=$(basename "$0")
    echo "ERROR: this script is meant to be executed with 'tpaexec ${script%.sh} …'" >&2
    exit 1
fi

_tpaexec_command() {
    REMAINDER=()
    DIRECTORIES=()
    while [[ $# -gt 0 ]]; do
        opt=$1
        shift

        case "$opt" in
            --include-tests-from)
                if [[ -z ${1:-''} ]]; then
                    error "$opt: No test directory specified"
                fi
                DIRECTORIES+=("$1")
                shift
                ;;

            --destroy-this-cluster)
                REMAINDER+=(-e "destroy_cluster=yes")
                ;;

            *)
                REMAINDER+=("$opt")
                ;;
        esac
    done

    set -- "${REMAINDER[@]:+${REMAINDER[@]}}" "$@"

    # If the first remaining argument is not an option, we take it as
    # the name of a test to run instead of 'default'. Other arguments
    # are passed unmodified to the playbook execution.

    test=default
    if [[ ${1:-''} && ! $1 =~ ^-.* ]]; then
        test=$1
        shift
    fi

    # We look for $test.yml in the cluster's tests directory, and fall
    # back to the built-in tests under architectures/lib/tests. Cluster
    # tests may be defined by the architecture (and symlinked in by the
    # configure command) or be created by hand.

    DIRECTORIES+=("$(pwd)/tests" "$TPA_DIR/architectures/lib/tests")

    testpath=""
    for dir in "${DIRECTORIES[@]}"; do
        path=$dir/$test
        if [[ -f $path.yml || -f $path.t.yml ]]; then
            testpath=$path
            break
        fi
    done

    if [[ -z "$testpath" ]]; then
        echo "ERROR: couldn't find a test named $test in any of the following directories:"
        for dir in "${DIRECTORIES[@]}"; do
            echo "    $dir"
        done
        exit 1
    fi

    if [[ -f "$testpath.t.yml" ]]; then
        output=$(mktemp -d "/tmp/$(basename "$testpath")-XXXXXXXXXX")
        "$TPA_DIR"/architectures/lib/compile-test "$testpath.t.yml" "$output" \
            --steps-from "$TPA_DIR"/architectures/lib/test-steps \
            --steps-from "$(pwd)"/test-steps
        testpath="$output/index.yml"
    fi

    time playbook "$TPA_DIR"/architectures/lib/commands/test.yml -e testpath="$testpath" "$@"
}
