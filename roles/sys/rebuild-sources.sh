#!/usr/bin/env bash
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

shopt -s nullglob

for file in /etc/tpa/rebuild-scripts/*.sh; do
    "${file}"
done

if systemctl is-active postgres; then
    systemctl restart postgres
fi
