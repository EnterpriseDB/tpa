set -eu

platform=${platform:-aws}
region=${region:-eu-west-1}
instance_type=${instance_type:-t2.micro}
if [[ ${distribution:=Debian} != *-minimal ]]; then
    distribution="$distribution${minimal:-}"
fi
