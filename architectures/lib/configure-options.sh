set -eu

case "$opt" in
    # These options set variables that are used by the configure script
    # directly (after architectures/lib/configure-defaults.sh sets the
    # default values, if applicable).

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
    --root-volume-size)
        root_volume_size=${1:?Root volume size not specified}
        shift
        ;;
    --minimal)
        minimal=-minimal
        ;;

    # These options export environment variables that are interpreted by
    # architectures/lib/subnets.

    --subnet-pattern)
        export SUBNET_PATTERN=${1:?Subnet pattern not specified}
        shift
        ;;

    --exclude-subnets-from)
        export SUBNET_EXCLUSIONS=${1:?Subnet exclusion directory not specified}
        type realpath &>/dev/null && SUBNET_EXCLUSIONS=$(realpath $SUBNET_EXCLUSIONS)
        shift
        ;;

    # These options export environment variables that are interpreted by
    # architectures/lib/cluster-vars.

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

    # These options export environment variables that are interpreted by
    # architectures/lib/cluster-tags.

    --owner)
        export CLUSTER_TAGS_OWNER=${1:?Owner not specified}
        shift
        ;;

    # These options export environment variables that are interpreted by
    # architectures/lib/hostnames.

    --hostnames-from)
        export HOSTNAMES_FROM=${1:?Hostname list file not specified}
        type realpath &>/dev/null && HOSTNAMES_FROM=$(realpath $HOSTNAMES_FROM)
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
