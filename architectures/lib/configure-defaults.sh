set -eu

cluster_name=$(basename $cluster)
platform=${platform:-aws}
region=${region:-eu-west-1}
instance_type=${instance_type:-t2.micro}
if [[ ${distribution:=Debian} != *-minimal ]]; then
    distribution="$distribution${minimal:-}"
fi

root_volume_size=${root_volume_size:-16}
postgres_volume_size=${postgres_volume_size:-16}
barman_volume_size=${barman_volume_size:-32}

image=$($libdir/image $distribution $platform $architecture)
eval $image
