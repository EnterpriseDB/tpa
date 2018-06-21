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
    --postgres-version)
        export POSTGRES_VERSION=${1:?Postgres major version not specified}
        shift
        ;;
    --postgres-package-version)
        export POSTGRES_PACKAGE_VERSION=${1:?Postgres package version not specified}
        shift
        ;;
    --repmgr-package-version)
        export REPMGR_PACKAGE_VERSION=${1:?repmgr package version not specified}
        shift
        ;;
    --barman-package-version)
        export BARMAN_PACKAGE_VERSION=${1:?repmgr package version not specified}
        shift
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
