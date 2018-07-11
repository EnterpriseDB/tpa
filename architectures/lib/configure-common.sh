IFS=$' \t\n'
set -eu

archdir=$(dirname $0)
libdir=$(dirname $0)/../lib

cluster=${1:?"No cluster directory specified (please run 'tpaexec configure clustername …' instead)"}
shift

error() {
    echo "ERROR: $@" >&2
    exit 1
}
