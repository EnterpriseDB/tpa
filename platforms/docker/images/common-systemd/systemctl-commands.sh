#!/bin/bash
set -e -u -x
export SYSTEMD_COLORS=0
source /etc/os-release

# Don't try to run a full system in the container
systemctl enable basic.target
systemctl set-default basic
systemctl preset-all

installedunits=$( systemctl list-unit-files | head -n -1 | tail -n -1 | cut -f1 -d ' ')

UNITS_TO_DISABLE=" machines.target network-pre.target network.target
  remote-fs-pre.target remote-fs.target swap.target
  systemd-hwdb-update.service systemd-readahead-collect.service
  systemd-readahead-replay.service systemd-readahead-done.timer
  systemd-readahead-done.service
  proc-sys-fs-binfmt_misc.mount sys-kernel-config.mount
  sys-kernel-debug.mount
  systemd-ask-password-console.path systemd-ask-password-wall.path
"

UNITS_TO_MASK="
	getty.target console-getty.service container-getty@.service
	getty-pre.target getty@.service serial-getty@.service
	time-sync.target
	system-logind.service
	sys-fs-fuse-connections.mount
"

for target in $UNITS_TO_DISABLE ;
do
	# need to check a unit is installed before trying to disable it
	if [[ " ${installedunits[@]} " =~ " $target " ]] ; then
		systemctl disable $target
	fi
done

for target in $UNITS_TO_MASK ;
do
	systemctl mask $target
done

if [ $ID = "ubuntu" ]
then
    systemctl disable apt-daily-upgrade.timer
    systemctl disable motd-news.timer
fi

[ -e /sbin/init ] || ln -s /bin/systemd /sbin/init
