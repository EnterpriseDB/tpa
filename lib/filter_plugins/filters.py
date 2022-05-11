#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import copy
import csv
import re
import sys
import shlex
import os.path
from collections.abc import Mapping, MutableMapping

from jinja2.runtime import StrictUndefined
from ansible.errors import AnsibleFilterError
from six import text_type

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


def index_list_of_dicts(obj, key=None, recursive=False):
    """
    Takes a list of dicts and creates a dictionary with keys using the given key name in the dict.

    For example:
        >>> obj = [{'Name': 'foo', 'attr': 123}, {'Name': 'bar', 'attr': 456}]
        >>> index_list_of_dicts(obj, 'Name')
        {'foo': {'Name': 'foo', 'attr': 123}, 'bar': {'Name': 'bar', 'attr': 456}}

    If key name is not defined the index of the list is used as the key name:
        >>> obj = [{'Name': 'foo', 'attr': 123}, {'Name': 'bar', 'attr': 456}]
        >>> index_list_of_dicts(obj)
        {0: {'Name': 'foo', 'attr': 123}, 1: {'Name': 'bar', 'attr': 456}}

    """
    ret_dict = {}
    if recursive:

        def func(a):
            return index_list_of_dicts(a, key, recursive)

    else:

        def func(a):
            return a

    if isinstance(obj, list):
        for (
            index,
            item,
        ) in enumerate(obj):
            if isinstance(item, MutableMapping):
                if key is not None:
                    ret_dict[item[key]] = func(item)
                else:
                    ret_dict[index] = func(item)
            else:
                ret_dict[index] = func(item)
    elif isinstance(obj, MutableMapping):
        ret_dict.update({k: func(v) for k, v in obj.items()})
    else:
        return obj

    return ret_dict


def pyformat_hostvars(hostname, format_str, hostvars):
    """
    Takes a hostname, hostvars, and a string with {references} to attributes in
    hostvars, and returns the .format()ed string
    """
    return format_str.format(**hostvars.get(hostname, {}))


def select_by_hostvar(hostnames, hostvars, varname, value):
    """
    Takes a list of hostnames, hostvars, the name of a variable, and a value to
    compare with, and returns those hostnames for which the variable is set to
    the given value in hostvars.
    """
    results = []
    for h in hostnames:
        v = hostvars[h].get(varname)
        if v == value:
            results.append(h)

    return results


class FilterModule(object):
    def filters(self):
        return {
            "try_subkey": try_subkey,
            "doublequote": doublequote,
            "upstream_root": upstream_root,
            "instance_with_backup_of": instance_with_backup_of,
            "remove_keys": remove_keys,
            "extract_keys": extract_keys,
            "packages_for": packages_for,
            "members_of": members_of,
            "from_csv": from_csv,
            "pyformat": pyformat,
            "pyformat_attr": pyformat_attr,
            "apply_format": apply_format,
            "backup_slot_name": backup_slot_name,
            "contains": contains,
            "abspath_to": abspath_to,
            "cmdline": cmdline,
            "sort_by_node": sort_by_node,
            "dict_format": dict_format,
            "ternary_format": ternary_format,
            "physical_replication_group": physical_replication_group,
            "dictify": dictify,
            "list2idxdict": index_list_of_dicts,
            "pyformat_hostvars": pyformat_hostvars,
            "split": text_type.split,
            "select_by_hostvar": select_by_hostvar,
            "joinpath": os.path.join,
        }
