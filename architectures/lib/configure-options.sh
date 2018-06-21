set -eu

minimal=

case "$opt" in
    --platform)
        platform=${1:?Platform name not specified}
        shift
        ;;
    --region)
        region=${1:?Region name not specified}
        shift
        ;;
    --subnet)
        subnet=${1:?Subnet address/mask not specified}
        shift
        ;;
    --instance-type)
        instance_type=${1:?Instance type not specified}
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
region=${region:-eu-west-1}
instance_type=${instance_type:-t2.micro}
if [[ ${distribution:=Debian} != *-minimal ]]; then
    distribution="$distribution$minimal"
fi
