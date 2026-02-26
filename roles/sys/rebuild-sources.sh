#!/usr/bin/env bash
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

shopt -s nullglob
set -e

for file in /etc/tpa/rebuild-scripts/*.sh; do
    "${file}"
done

if systemctl is-active postgres; then
    systemctl restart postgres
fi
