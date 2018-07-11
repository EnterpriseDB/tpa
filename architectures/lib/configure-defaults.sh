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

image=$($libdir/image $distribution $platform $architecture)
eval $image

vars+=([image_name]=$image_name [image_owner]=$image_owner [image_user]=$image_user)
