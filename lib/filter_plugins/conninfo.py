#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from ansible.errors import AnsibleFilterError
from typing import Dict, List


def parse_conninfo(conninfo: str, key: str = None) -> Dict[str, str]:
    """
    Takes a conninfo string and returns a dict of the settings it represents; or
    if given a key, returns the value if the key is specified, or None.
    """

    settings = {}
    for str in conninfo.strip().split(" "):
        parts = [x.strip() for x in str.strip().split("=", 1)]

        v = None
        if len(parts) == 2:
            v = parts[1]
            while (v.startswith("'") and v.endswith("'")) or (
                v.startswith('"') and v.endswith('"')
            ):
                v = v[1:-1]

        settings[parts[0]] = v

    if key:
        return settings.get(key, None)

    return settings


def conninfo_string(d: Dict[str, str]) -> str:
    """
    Returns a conninfo string assembled from the keys and values in the dict d.
    Values are single-quoted if needed.
    """

    def _quote(s):
        if not (" " in s or "\\" in s or "'" in s or s == ""):
            return s
        return "'%s'" % str(s).replace("\\", "\\\\").replace("'", "\\'")

    s = []
    for (k, v) in d.items():
        s.append("%s=%s" % (k, _quote(str(v))))
    return " ".join(s)


def dbname(conninfo: str, dbname: str = "postgres", **kwargs) -> str:
    """
    Given a conninfo string, a dbname, and optional additional key=value
    settings, returns a new conninfo string that includes the dbname and other
    settings.
    """
    parts = parse_conninfo(conninfo)
    parts["dbname"] = dbname
    for k in kwargs:
        parts[k] = kwargs[k]
    return conninfo_string(parts)


def multihost_conninfo(conninfos: List[str]) -> str:
    """
    Takes a list of conninfo strings and returns a conninfo with the host and
    port set to comma-separated strings of the hosts and ports in the original
    list (or port set to a single value if all conninfos have the same value),
    and all other connection parameters unmodified.

    Each conninfo string must specify the host and port explicitly (i.e., there
    are valid inputs with implicit settings that libpq would accept, but which
    this function will not), and all other parameters must be identical.

    https://www.postgresql.org/docs/14/libpq-connect.html#LIBPQ-MULTIPLE-HOSTS
    """

    result = {}
    all_hosts = []
    all_ports = []

    # We step through the inputs, collecting lists of hosts and ports, and
    # comparing connection parameters for successive entries in the list to
    # ensure that they don't say anything different.

    for item in conninfos:
        params = parse_conninfo(item)
        all_hosts.append(params['host'])
        all_ports.append(params['port'])
        del params['host']
        del params['port']
        if result and result != params:
            raise AnsibleFilterError(
                f"|multihost_conninfo expects DSNs that differ only in "
                f"host/port; got '{item}' vs. '{conninfos[0]}'"
            )
        result = params

    result['host'] = ','.join(all_hosts)
    if len(set(all_ports)) == 1:
        result['port'] = all_ports[0]
    else:
        result['port'] = ','.join(all_ports)
    return conninfo_string(result)


# Given a subscription (and access to hostvars), this function returns a
# provider_dsn for the subscription, which may be an explicitly specified
# provider_dsn, or derived from the name of a publication (and an optional
# instance name, if required for disambiguation).
#
# sub:
#   provider_dsn: "host=… dbname=…"
#   # OR:
#   publication:
#     name: publication_name
#     instance: instance_name
#
# See postgres/pglogical/tasks/subscribe.yml for context.


def provider_dsn(sub, hostvars):
    provider_dsn = sub.get("provider_dsn")
    if provider_dsn:
        return provider_dsn

    publication = sub.get("publication")
    if not publication:
        raise AnsibleFilterError(
            "Subscription %s does not specify .publication.name(+instance)"
            % sub.get("name")
        )

    name = publication.get("name")
    if not name:
        raise AnsibleFilterError(
            "Subscription %s does not specify .publication.name" % sub.get("name")
        )

    providers = list(hostvars.keys())
    instance = publication.get("instance")
    if instance:
        providers = [instance]

    matches = []
    for h in providers:
        vars = hostvars.get(h, {})
        publications = vars.get("publications", [])
        for p in publications:
            if p.get("type") == "pglogical" and p.get("name") == name:
                matches.append(dbname(vars.get("node_dsn"), p.get("database")))

    if not matches:
        raise AnsibleFilterError(
            "Publication %s (subscription=%s) not found" % (name, sub.get("name"))
        )
    if len(matches) != 1:
        raise AnsibleFilterError(
            "Publication %s (subscription=%s) not unique; specify instance"
            % (name, sub.get("name"))
        )

    return matches[0]


class FilterModule(object):
    def filters(self):
        return {
            "parse_conninfo": parse_conninfo,
            "conninfo_string": conninfo_string,
            "dbname": dbname,
            "provider_dsn": provider_dsn,
            "multihost_conninfo": multihost_conninfo,
        }
