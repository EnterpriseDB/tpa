#!/bin/sh

repmgr standby promote -f /etc/repmgr/repmgr.conf

# On successful promotion, failover the elastic IP to itself

if [ "$?" -eq "0" ]; then
	python2.7 /etc/repmgr/assign_eip.py
fi
