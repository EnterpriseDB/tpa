#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import copy
import csv
import re
import sys
import shlex
import os.path
from jinja2.runtime import StrictUndefined
from ansible.errors import AnsibleFilterError
from collections.abc import Mapping

# Based on PR ansible/ansible#11083, this filter takes a container and a subkey
# ('x.y.z', or [x,y,z]) and a default value, and returns container.x.y.z or the
# default value if any of the levels is undefined.


def try_subkey(container, keys, default=None):
    try:
        v = container
        if isinstance(keys, str):
            keys = keys.split(".")
        for key in keys:
            if isinstance(v, list):
                if isinstance(key, int):
                    v = v[key]
                else:
                    # Can't index a list by a non-integer, and can't call .get
                    # on lists below either.
                    raise
            else:
                v = v.get(key, default)
        if isinstance(v, StrictUndefined):
            v = default
        return v
    except:
        return default


# Given 'foo', returns '"foo"'. Blindly converts each embedded double quote in
# the string to '\"'. Caveat emptor.


def doublequote(str):
    return '"%s"' % str.replace('"', '"')


# Given a hostname and hostvars, returns the name of the earliest ancestor that
# doesn't have an upstream defined.


def upstream_root(h, hostvars):
    while h in hostvars and hostvars[h].get("upstream", "") != "":
        h = hostvars[h].get("upstream")
    return h


# Given a list of hostnames and the names of a primary instance and some other
# instance (and a copy of hostvars), returns the name of an instance that has
# «backup: xxx» defined and is descended from the primary. It will prefer the
# first backed-up instance in the same region as "somehost", otherwise return
# the first backed-up instance. Returns None if no instances match.


def instance_with_backup_of(hosts, primary, somehost, hostvars):
    candidates = []

    for h in hosts:
        if (
            hostvars[h].get("backup", "") != ""
            and upstream_root(h, hostvars) == primary
        ):
            candidates.append(h)

    for backedup in candidates:
        if hostvars[backedup].get("region", "left") == hostvars[somehost].get(
            "region", "right"
        ):
            return backedup
    if candidates:
        return candidates[0]

    return None


# Takes a dict and a list of keys and returns a new dict which has none of the
# keys in the list.


def remove_keys(d, keys):
    if not isinstance(d, dict):
        raise AnsibleFilterError(
            "|remove_keys takes a dict as its first argument, got " + type(d)
        )

    if not isinstance(keys, list):
        raise AnsibleFilterError(
            "|remove_keys takes a list as its second argument, got " + type(keys)
        )

    d2 = copy.deepcopy(d)
    for k in keys:
        if k in d2:
            del d2[k]

    return d2


# Takes a dict and a list of keys and returns a new dict which has only the keys
# in the list that have defined values.


def extract_keys(d, keys):
    if not isinstance(d, Mapping):
        raise AnsibleFilterError(
            "|extract_keys takes a dict as its first argument, got " + type(d)
        )

    if not isinstance(keys, list):
        raise AnsibleFilterError(
            "|extract_keys takes a list as its second argument, got " + type(keys)
        )

    d2 = {}
    for k in keys:
        if d.get(k):
            d2[k] = d.get(k)

    return d2


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


# Given a hash that maps os names to package lists, the name of an os, and an
# optional version suffix, this function returns a list of packages for the
# given os, with the version suffix applied (if provided).


def packages_for(packages, os, version=None):
    ret = []

    for p in packages.get(os, []):
        if not (version is None or isinstance(version, StrictUndefined)):
            sep = "="
            if os == "RedHat":
                sep = "-"
            p = "%s%s%s" % (p, sep, version)
        ret.append(p)

    return ret


# Given a hash that maps group names to lists of group members (such as the
# global variable "groups"), a group name, and a list of groups to exclude, this
# function returns the members of the named group that are not members of any of
# the excluded groups. Empty and undefined groups are silently ignored.
#
# For example, groups|members_of('role_a', not_in=['role_b','role_c']) would
# return hosts in the group role_a that were not in either groups role_b or
# role_c (as if there were a group named 'role_a_but_not_b_or_c').


def members_of(groups, group, not_in=[]):
    members = set(groups.get(group, []))
    excluded = set()
    for g in not_in:
        excluded |= set(groups.get(g, []))
    return list(members - excluded)


# Given a conninfo string, a dbname, and optional additional key=value settings,
# returns a new conninfo string that includes the dbname and other settings.
# Does not try to remove existing settings from the conninfo, since later
# entries override earlier ones anyway.


def dbname(conninfo, dbname="postgres", **kwargs):
    extra = ["dbname=%s" % dbname]
    for k in kwargs:
        extra.append("%s=%s" % (k, kwargs[k]))
    return conninfo + " " + " ".join(extra)


# Given a line containing comma-separated values and a list of column names,
# this filter returns a hash that maps from column names to the corresponding
# values from the input line.


def from_csv(line, column_names):
    for values in csv.reader([line]):
        return dict(list(zip(column_names, values)))


# Formats the given value using Python's .format() function, passing on any
# additional arguments, e.g., ``'{a} and {b}'|format(a=42, b='xyzzy')``.
#
# The built-in jinja2 |format filter does _not_ use Python's .format() function
# and only supports % escapes, not {name} interpolation.


def pyformat(value, **kwargs):
    return value.format(**kwargs)


# Given a container and an attribute, returns a container with the attribute's
# value replaced with the result of calling .format() on the value along with
# any additional arguments provided.


def pyformat_attr(container, attr, **kwargs):
    c = copy.deepcopy(container)
    a = c.get(attr)
    if a:
        c[attr] = a.format(**kwargs)
    return c


# Given a format string and some input values, returns the result of applying
# format() to the string with the given values. For example,
#
# x.keys()|map('apply_format', '{0} := %s')|list


def apply_format(input, format_string, *more):
    args = [input]
    if isinstance(input, list):
        args = input
    if more:
        args.append(*more)
    return format_string.format(*args)


# Given the name of a barman host, returns a string suitable for use as the name
# of a replication slot used for backups by the barman host.


def backup_slot_name(barman_hostname):
    return "backup_%s" % re.sub("-", "_", re.sub("\\..*", "", barman_hostname))


# Returns True if all of the one or more given values are in the container, and
# False otherwise.


def contains(container, *values):
    for v in values:
        if v not in container:
            return False
    return True


# Returns the given path if it is absolute, otherwise returns the path prefixed
# with the given directory path (assumed to be absolute).


def abspath_to(directory, path):
    return os.path.join(directory, os.path.expanduser(path))


# Returns a string that represents sys.argv[] with some unnecessary noise
# omitted. Takes the playbook_dir as an argument.


def cmdline(playbook_dir):
    args = sys.argv

    # bin/tpaexec:playbook() executes ansible-playbook with a predictable
    # sequence of arguments, which we can reduce to the bare essentials.

    if (
        os.path.basename(args[0]) == "ansible-playbook"
        and args[1] == "-e"
        and args[2].startswith("tpa_dir=")
        and args[3] == "-e"
        and args[4].startswith("cluster_dir=")
        and args[5] == "-i"
        and args[6] == "inventory"
        and args[7] == "--vault-password-file"
        and args[8] == "vault/vault_pass.txt"
    ):

        tpaexec = "tpaexec"

        tpa_dir = args[2].replace("tpa_dir=", "")
        if tpa_dir not in ["/opt/EDB/TPA", "/opt/2ndQuadrant/TPA"]:
            tpaexec = os.path.join(tpa_dir, "bin/tpaexec")

        cluster_dir = args[4].replace("cluster_dir=", "")

        playbook = args[9]
        if playbook.startswith(cluster_dir):
            playbook = os.path.relpath(playbook, start=cluster_dir)
        elif playbook.startswith(tpa_dir):
            playbook = os.path.relpath(playbook, start=tpa_dir)

        args = [tpaexec, "playbook", cluster_dir, playbook] + args[10:]

    # It's better to output "''" than ''"'"''"'"''
    def _shortest_quote(x):
        sq = shlex.quote(x)

        if x != sq:
            dq = '"' + x.replace('"', '"') + '"'
            x = dq if len(dq) < len(sq) else sq

        return x

    return " ".join([_shortest_quote(x) for x in args])


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


# Returns the given list of hostnames, sorted by the numeric value of their
# node id


def sort_by_node(hosts, hostvars):
    def node_for_host(host):
        return hostvars[host].get("node")

    sorted_hosts = sorted(hosts, key=node_for_host)
    return sorted_hosts


# Returns a list consisting of lines resulting from formatting the format_string
# with each key and corresponding value from the given dict. The format string
# may include {key}, {value}, and any other names given as optional keyword
# arguments.


def dict_format(d, format_string, **kwargs):
    results = []
    for k in d:
        results.append(format_string.format(key=k, value=d[k], **kwargs))
    return results


# Given a value, an expression, a true string, a false string, and optional
# kwargs, returns the result of formatting the true string or false string,
# depending on whether the expression is true or false, with the value and
# kwargs.
#
# somelist|map('ternary_format', x == y,
#   'x is y and {value} is {colour}',
#   'x is not y and {value} is {colour}',
#   colour='purple'
# )


def ternary_format(val, expr, true_string, false_string, **kwargs):
    s = true_string if expr else false_string
    return s.format(value=val, **kwargs)


# Given the name of an instance (and hostvars), returns a list of names of
# instances that are related by physical replication, starting with the primary
# (cf. upstream_root above), followed by replicas/descendants (and including the
# instance itself) based on their upstream setting. Returns an empty list if the
# instance is not part of such a replication group.


def physical_replication_group(h, hostvars):
    # First, we collect the names, upstream, and direct descendants (according
    # to the upstream setting) of all primary and replica instances.

    instances = {}
    for k in hostvars:
        v = hostvars[k]

        role = v.get("role") or []
        if not ("primary" in role or "replica" in role):
            continue

        if k not in instances:
            instances[k] = {}
        if "descendants" not in instances[k]:
            instances[k]["descendants"] = []

        upstream = v.get("upstream")
        if upstream:
            if upstream not in instances:
                instances[upstream] = {}
            if "descendants" not in instances[upstream]:
                instances[upstream]["descendants"] = []
            instances[upstream]["descendants"].append(k)

        instances[k]["upstream"] = upstream

    # Starting with the given instance, find the most-upstream instance and
    # return it and all its descendants.

    while h in instances and instances[h]["upstream"]:
        h = instances[h]["upstream"]

    def instance_and_all_descendants(i):
        if i not in instances:
            return []

        family = [i]
        for d in instances[i]["descendants"]:
            family += instance_and_all_descendants(d)

        return family

    return instance_and_all_descendants(h)


# Given an item and a key, returns a dict that maps from the key to the item.
# Meant to be used as ['x','y','z']|map('dictify', 'name')|list to obtain
# [{'name': 'x'}, {'name': 'y'}, {'name': 'z'}].


def dictify(item, key="name"):
    return {key: item}


class FilterModule(object):
    def filters(self):
        return {
            "try_subkey": try_subkey,
            "doublequote": doublequote,
            "upstream_root": upstream_root,
            "instance_with_backup_of": instance_with_backup_of,
            "remove_keys": remove_keys,
            "extract_keys": extract_keys,
            "parse_conninfo": parse_conninfo,
            "conninfo_string": conninfo_string,
            "packages_for": packages_for,
            "members_of": members_of,
            "dbname": dbname,
            "from_csv": from_csv,
            "pyformat": pyformat,
            "pyformat_attr": pyformat_attr,
            "apply_format": apply_format,
            "backup_slot_name": backup_slot_name,
            "contains": contains,
            "abspath_to": abspath_to,
            "cmdline": cmdline,
            "provider_dsn": provider_dsn,
            "sort_by_node": sort_by_node,
            "dict_format": dict_format,
            "ternary_format": ternary_format,
            "physical_replication_group": physical_replication_group,
            "dictify": dictify,
        }
