# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

set -eu

vars[architecture]=$architecture
vars[cluster_name]=${cluster_name:=$(basename $cluster)}
vars[platform]=${platform:=aws}
vars[region]=${region:=eu-west-1}
vars[instance_type]=${instance_type:=t2.micro}
vars[root_volume_size]=${root_volume_size:=16}
vars[postgres_volume_size]=${postgres_volume_size:=16}
vars[barman_volume_size]=${barman_volume_size:=32}

if [[ ${distribution:=Debian} != *-minimal ]]; then
    distribution="$distribution${minimal:-}"
fi

if [[ $platform != bare ]]; then
    eval "vars+=($($libdir/image $distribution $platform $architecture))"
fi

hostnames=(zero $($libdir/hostnames $instances))
vars+=([hostnames]=$(IFS=, && echo "[${hostnames[*]}]"))
