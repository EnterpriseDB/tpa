#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

from typing import Dict, List, Any


def bdr_node_kind(role: List[str]) -> str:
    """Returns a BDR node_kind value corresponding to the given the list of
    roles for an instance.
    """
    if "witness" in role:
        return "witness"
    elif "subscriber-only" in role:
        return "subscriber-only"
    elif "standby" in role:
        return "standby"
    else:
        return "data"


def bdr_node_versions(hosts: List[str], hostvars: Dict[str, Any]) -> Dict[str, str]:
    """Given hostvars, returns a list of BDR major versions running on each of
    the given hostnames, assumed to be BDR instances that have already run
    cluster_discovery.

    If it can't retrieve the version for any host, it just moves on to the next
    one. So if the result has fewer keys than the number of hosts you passed in,
    then you know something went wrong.
    """
    versions = {}
    for h in hosts:
        hv = hostvars[h]
        try:
            bdr_database = hv["bdr_database"]
            bdr_database_facts = hv["cluster_facts"]["databases"][bdr_database]
            versions[h] = bdr_database_facts["bdr"]["bdr_version"]
        except KeyError:
            continue

    return versions


class FilterModule(object):
    def filters(self):
        return {
            "bdr_node_kind": bdr_node_kind,
            "bdr_node_versions": bdr_node_versions,
        }
