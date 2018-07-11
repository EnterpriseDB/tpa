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
