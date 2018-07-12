IFS=$' \t\n'
set -eu

declare -A vars

archdir=$(dirname $0)
libdir=$(dirname $0)/../lib

cluster=${1:?"No cluster directory specified (please run 'tpaexec configure clustername …' instead)"}
shift

mkdir $cluster
trap "rm -rf $cluster" ERR

error() {
    echo "ERROR: $@" >&2
    exit 1
}

template() {
    PYTHONPATH=${ANSIBLE_HOME:+$ANSIBLE_HOME/lib:}${PYTHONPATH:-""} \
    ANSIBLE_FILTER_PLUGINS=${ANSIBLE_FILTER_PLUGINS:+$ANSIBLE_FILTER_PLUGINS:}$TPA_DIR/lib/filter_plugins \
    ANSIBLE_LOOKUP_PLUGINS=${ANSIBLE_LOOKUP_PLUGINS:+$ANSIBLE_LOOKUP_PLUGINS:}$TPA_DIR/lib/lookup_plugins \
    ANSIBLE_TEST_PLUGINS=${ANSIBLE_TEST_PLUGINS:+$ANSIBLE_TEST_PLUGINS:}$TPA_DIR/lib/test_plugins \
    $libdir/template.py $1 $2 $libdir/templates
}
