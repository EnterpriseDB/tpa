#!/bin/bash
set -e -u -x
export SYSTEMD_COLORS=0
source /etc/os-release

if [[ $ID = "debian" || $ID = "ubuntu" ]]; then
    apt-get update -y && apt-get install -y systemd
fi

# Don't try to run a full system in the container
systemctl enable basic.target
systemctl set-default multi-user
systemctl preset-all

UNITS_TO_DISABLE=(
    machines.target network-pre.target network.target
    remote-fs-pre.target remote-fs.target swap.target
    systemd-hwdb-update.service systemd-readahead-collect.service
    systemd-readahead-replay.service systemd-readahead-done.timer
    systemd-readahead-done.service
    proc-sys-fs-binfmt_misc.mount sys-kernel-config.mount
    sys-kernel-debug.mount
    systemd-ask-password-console.path systemd-ask-password-wall.path
)

UNITS_TO_MASK=(
    getty.target console-getty.service container-getty@.service
    getty-pre.target getty@.service serial-getty@.service
    time-sync.target
    system-logind.service
    sys-fs-fuse-connections.mount
)

# We can't just disable all the units we don't want; we have to check
# which ones exist and only disable those. (But we can mask all the
# units we like, whether they exist or not.)

matches=$(systemctl list-unit-files "${UNITS_TO_DISABLE[@]}"|sed -n '1d;/^$/d;$d;p'|awk '{print $1}')
if [[ -n $matches ]]; then
    systemctl disable $matches
fi

systemctl mask "${UNITS_TO_MASK[@]}"

if [[ $ID = "ubuntu" ]]; then
    systemctl disable apt-daily-upgrade.timer
    systemctl disable motd-news.timer
fi

[ -e /sbin/init ] || ln -s /bin/systemd /sbin/init
