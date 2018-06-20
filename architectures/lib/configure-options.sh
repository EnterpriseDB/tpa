set -eu

minimal=

case "$opt" in
    --platform)
        platform=${1:?Platform name not specified}
        shift
        ;;
    --distribution|--os)
        distribution=${1:?Distribution name not specified}
        shift
        ;;
    --minimal)
        minimal=-minimal
        ;;
    --hostnames-from)
        hostnames_args+=(${1:?Hostname list file not specified})
        shift
        ;;
    --hostnames-pattern)
        if [[ ${#hostnames_args[@]} != 1 ]]; then
            error "--hostnames-pattern must come after --hostnames-from"
        fi
        hostnames_args+=(${1:?Hostname pattern not specified})
        shift
        ;;
    *)
        error "unrecognised parameter: $opt"
        ;;
esac

platform=${platform:-aws}
if [[ ${distribution:=Debian} != *-minimal ]]; then
    distribution="$distribution$minimal"
fi
