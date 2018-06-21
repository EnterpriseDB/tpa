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
        export HOSTNAMES_FROM=${1:?Hostname list file not specified}
        shift
        ;;
    --hostnames-pattern)
        export HOSTNAMES_PATTERN=${1:?Hostname pattern not specified}
        shift
        ;;
    --hostnames-sorted-by)
        export HOSTNAMES_SORTED_BY=${1:?Hostname sort option not specified}
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
