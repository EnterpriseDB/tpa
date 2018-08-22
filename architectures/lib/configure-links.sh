# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

set -eu

ln -sf $archdir/deploy.yml $cluster
if [[ -d $archdir/commands ]]; then
    mkdir $cluster/commands
    for f in $archdir/commands/*; do
        ln -sf $f $cluster/commands
    done
fi
rm -f -- "$v"
