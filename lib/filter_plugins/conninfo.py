#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from ansible.errors import AnsibleFilterError

# Takes a conninfo string and returns a dict of the settings it represents, or
# if given a key, returns the value if the key is specified, or None.


def parse_conninfo(conninfo, key=None):

    settings = {}
    for str in conninfo.split(" "):
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


# Returns a conninfo string assembled from the keys and values in the dict d.
# Values are single-quoted if needed. Order of elements is not guaranteed.


def conninfo_string(d):
    def _quote(s):
        if not (" " in s or "\\" in s or "'" in s or s == ""):
            return s
        return "'%s'" % str(s).replace("\\", "\\\\").replace("'", "\\'")

    s = []
    for (k, v) in d.items():
        s.append("%s=%s" % (k, _quote(str(v))))
    return " ".join(s)


# Given a conninfo string, a dbname, and optional additional key=value settings,
# returns a new conninfo string that includes the dbname and other settings.
# Does not try to remove existing settings from the conninfo, since later
# entries override earlier ones anyway.


def dbname(conninfo, dbname="postgres", **kwargs):
    extra = ["dbname=%s" % dbname]
    for k in kwargs:
        extra.append("%s=%s" % (k, kwargs[k]))
    return conninfo + " " + " ".join(extra)


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
        }
