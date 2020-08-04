#!/bin/bash
set -e -u -x
export SYSTEMD_COLORS=0
# Don't try to run a full system in the container
systemctl enable basic.target
systemctl set-default basic
systemctl preset-all
# Make sure we don't try to hijack gettys even if the user runs systemd in a
# privileged container. We don't want it taking over the host TTYs.
systemctl mask getty.target
systemctl mask console-getty.service
systemctl mask container-getty@.service
systemctl mask getty-pre.target
systemctl mask getty@.service
systemctl mask serial-getty@.service
# Don't mess with the clock
systemctl mask time-sync.target
# Unnecessary in a container:
systemctl disable machines.target
systemctl disable network-pre.target
systemctl disable network.target
systemctl disable remote-fs-pre.target
systemctl disable remote-fs.target
systemctl disable swap.target
systemctl disable systemd-hwdb-update.service
systemctl disable systemd-readahead-collect.service
systemctl disable systemd-readahead-replay.service
systemctl disable systemd-readahead-done.timer
systemctl disable systemd-readahead-done.service
# We don't need logins at all in a container
systemctl mask systemd-logind.service
# Don't try to set up fuse
systemctl mask sys-fs-fuse-connections.mount
# Prune unnecessary services
systemctl disable proc-sys-fs-binfmt_misc.mount
systemctl disable sys-kernel-config.mount
systemctl disable sys-kernel-debug.mount
systemctl disable systemd-ask-password-console.path
systemctl disable systemd-ask-password-wall.path

source /etc/os-release
# Ubuntu specific
if [ $ID = "ubuntu" ]
then
	systemctl disable apt-daily-upgrade.timer
	systemctl disable motd-news.timer
	ln -s /bin/systemd /sbin/init
fi
