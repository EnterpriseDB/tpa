IFS=$' \t\n'
set -eu

archdir=$(dirname $0)
libdir=$(dirname $0)/../lib
hostnames_args=()

cluster=${1:?"No cluster directory specified (please run this script via 'tpaexec config clustername …')"}
shift

error() {
    echo "ERROR: $@" >&2
    exit 1
}
