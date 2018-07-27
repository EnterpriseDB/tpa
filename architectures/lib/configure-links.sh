set -eu

ln -sf $archdir/deploy.yml $cluster
if [[ -d $archdir/commands ]]; then
    mkdir $cluster/commands
    for f in $archdir/commands/*; do
        ln -sf $f $cluster/commands
    done
fi
rm -f -- "$v"
