#!/usr/bin/env python
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from __future__ import print_function

import yaml
import os
import re
import random
import string

from ..exceptions import TestCompilerError


class TestCompiler(object):
    """
    The test compiler can transform an input file containing test specifications
    (in .t.yml format) into one or more Ansible playbooks to execute the desired
    tests.
    """

    def __init__(self, options=None):
        self.tests = []
        self.options = options or {}

    def read_input(self, infile):
        """
        Translates test specifications from the given file into a series of Test
        objects representing the Ansible plays required to implement the desired
        tests.
        """
        specs = read_yaml(infile)
        if not isinstance(specs, list):
            raise TestCompilerError(
                "expected a list of test specifications in YAML format"
            )

        for i, spec in enumerate(specs):
            if not isinstance(spec, dict):
                raise TestCompilerError("test #%s: not a dict" % i)
            if spec.get("test") is None:
                raise TestCompilerError("test #%s: no 'test' id specified" % i)

            self.tests.append(Test.compile(spec, self.options))

    def write_output(self, outdir):
        """
        Writes the compiler output into the given output directory (which must
        exist already), starting from index.yml and including additional files
        as required.
        """
        all_plays = []
        all_includes = {}

        for t in self.tests:
            for p in t.plays:
                all_plays.append(p)
            for i in t.includes:
                if i in all_includes:
                    raise TestCompilerError(
                        "include filename collision: %s (rerun)" % i
                    )
                all_includes[i] = t.includes[i]

        write_yaml(outdir, "index.yml", all_plays)
        for f in all_includes.keys():
            write_yaml(outdir, f, all_includes[f])


class Test(object):
    """
    Represents a single test specification in the form of a list of Ansible
    plays (and tasks therein) as well as optional include files (containing
    tasks).
    """

    def __init__(self):
        self.id = None
        self.plays = []
        self.includes = {}
        self.options = {}
        self.spec = {}
        self.test_group = ""
        self.test_options = {}

    @staticmethod
    def compile(spec, options):
        """
        Returns a Test object corresponding to the given test specification, or
        raises an exception if the specification is not valid.
        """
        t = Test()
        t.spec = spec
        t.options = options

        t.id = spec.get("test")
        t.test_group = "test_%s" % re.sub("[._/-]", "_", t.id)

        # We allow arbitrary keys to be set under options to control the
        # playbook generation in (as yet) unspecified ways.

        t.test_options = spec.get("options", {})
        if not isinstance(t.test_options, dict):
            raise TestCompilerError("%s: options: not a dict" % t.id)

        # The hosts list comprises notional host names (which make sense for the
        # purposes of the test, but are not necessarily assigned to real hosts)
        # and the conditions that a host must fulfil to play a role in the test.
        # We must create a play to perform the mapping.

        hosts = spec.get("hosts", [])
        if not isinstance(hosts, list):
            raise TestCompilerError("%s: hosts: not a list" % t.id)
        for h in hosts:
            if not (isinstance(h, dict) and len(h) == 1):
                raise TestCompilerError(
                    "%s: hosts: entry must map {hostlabel: [conditions]}" % t.id
                )

        t.append_play(
            {
                "name": "Identify hosts for test %s" % t.id,
                "hosts": "all",
                "vars": {"test_hosts": {}},
                "tasks": t.identify_hosts(hosts),
            }
        )

        # Next, we parse the list of steps to execute on the matched hosts and
        # generate a play from it targeting the hosts identified above.

        steps = spec.get("steps", [])
        if not isinstance(steps, list):
            raise TestCompilerError("%s: steps: not a list" % t.id)
        for s in steps:
            if not isinstance(s, dict):
                raise TestCompilerError("%s: steps: each entry must be a dict" % t.id)

        t.append_play(
            {
                "name": "Execute test %s" % t.id,
                "hosts": t.test_group,
                "tasks": t.translate_steps(steps),
            }
        )

        return t

    def append_play(self, attrs):
        """
        Creates a new play with the given attributes and appends it to the list
        of plays for this test.
        """
        p = {}
        p.update(self.test_options)
        p.update(
            {
                "any_errors_fatal": True,
                "max_fail_percentage": 0,
            }
        )
        p.update(attrs)
        self.plays.append(p)

    def include_tasks(self, tasks):
        """
        Creates a new include for this test with the given list of tasks, and
        returns the random name generated for the include file.
        """
        name = random_string(11) + ".yml"
        self.includes[name] = tasks
        return name

    def identify_hosts(self, hosts):
        """
        Given a list of host labels and conditions, this function returns tasks
        to assign real host names to each of the labels in such a way that all
        hosts agree on the assignment.
        """
        tasks = []

        for h in hosts:
            label = h.keys()[0]
            exprs = h[label]

            conditions = [
                "%s is not defined" % label,
                "item not in test_hosts.values()",
            ]

            for e in exprs:
                # has_role: x
                # has_role: x,y
                # has_role: [x,y]
                if "has_role" in e:
                    roles = e["has_role"]
                    if isinstance(roles, str):
                        roles = [r.strip() for r in roles.split(",")]
                    for r in roles:
                        conditions.append("'%s' in hostvars[item].role" % r)

                # has_vars:
                # - must_be_defined
                # - must_equal: foo
                elif "has_vars" in e:
                    _vars = e["has_vars"]
                    if not isinstance(_vars, list):
                        raise TestCompilerError("has_vars must specify a list")
                    for v in _vars:
                        if isinstance(v, str):
                            conditions.append("hostvars[item]['%s'] is defined" % v)
                        elif isinstance(v, dict) and len(v) == 1:
                            name = list(v.keys())[0]
                            conditions.append("hostvars[item]['%s'] is defined" % name)
                            conditions.append(
                                "hostvars[item]['%s'] == %s" % (name, v[name])
                            )
                        else:
                            raise TestCompilerError(
                                "has_vars: entry must be str or {var: value}"
                            )

                else:
                    conditions.append(e)

            tasks.append(
                {
                    "name": "Identify host for %s" % label,
                    "set_fact": {
                        label: "{{ item }}",
                        "test_hosts": "{{ test_hosts|combine({'%s': item}) }}" % label,
                    },
                    "with_items": "{{ ansible_play_hosts }}",
                    "when": conditions,
                }
            )

        tasks.append(
            {
                "group_by": {"key": self.test_group},
                "when": "inventory_hostname in test_hosts.values()",
            }
        )

        msg = "Expected %s hosts in group %s, got only {{ num_hosts }}"
        tasks.append(
            {
                "assert": {
                    "msg": msg % (len(hosts), self.test_group),
                    "that": "num_hosts|int == %s" % len(hosts),
                },
                "vars": {
                    "num_hosts": "{{ groups['%s']|length }}" % self.test_group,
                },
                "run_once": True,
            }
        )

        tasks.append({"debug": {"var": "test_hosts"}, "run_once": True})

        return tasks

    def translate_steps(self, steps):
        """
        Given a test group name (in the Ansible inventory sense) and a list of
        step definitions, this function returns tasks to execute the desired
        steps on the hosts in the group.
        """
        tasks = []

        for i, s in enumerate(steps):
            if not isinstance(s, dict):
                raise TestCompilerError("step #%s: not a dict" % i)

            t = {"vars": {}, "when": []}

            if "sleep" in s:
                t.update(
                    {
                        "pause": {"seconds": s["sleep"]},
                    }
                )

            elif "sh" in s:
                t.update(
                    {
                        "shell": s["sh"],
                    }
                )

            elif "block" in s:
                block = s["block"]
                if not isinstance(block, list):
                    raise TestCompilerError("every block must be a list of steps")

                substeps = self.translate_steps(block)
                t.update({"block": substeps})

            else:
                step = self.find_custom_step(s)
                if step is None:
                    raise TestCompilerError("unhandled step: %s" % s)
                t.update(step)

            # By default, every step runs on every host, but you can set 'hosts'
            # on the step to specify that it should run on one host, a list of
            # hosts, or 'any' to pick a random host.
            #
            # We set step_hosts and add an 'inventory_hostname in step_hosts'
            # condition on the generated task to restrict execution.

            if "hosts" in s:
                hosts = s["hosts"]
                if isinstance(hosts, str) and hosts != "any":
                    hosts = [hosts]

                # To handle 'any', we must create some extra tasks.
                #
                # We can't set step_hosts to "{{ all_hosts|random_sample(1) }}"
                # or something like that, because each host would evaluate that
                # expression and come up with a different answer (and multiple
                # hosts could decide to run the step).
                #
                # Instead, we create a temporary file on localhost, write the
                # candidate host names to it (which requires locking), sort it
                # randomly, and have all hosts read the first line (or N lines,
                # if required in future).
                #
                # Finally, to aid in debugging the decision, we use another task
                # to set_fact step_hosts, rather than set it in t['vars'].

                if hosts == "any":
                    tasks.append(
                        {
                            "name": "Create empty step_hosts file",
                            "tempfile": {"prefix": "step_hosts."},
                            "register": "tmpfile",
                            "delegate_to": "localhost",
                            "run_once": True,
                        }
                    )

                    cmd = "echo {{ inventory_hostname }} >> {{ tmpfile.path }}"
                    tasks.append(
                        {
                            "name": "Collect hostnames in step_hosts",
                            "shell": "(flock 9; %s) 9<{{ tmpfile.path }}" % cmd,
                            "delegate_to": "localhost",
                        }
                    )

                    any_host = "sort -R {{ tmpfile.path }}|head -1"
                    tasks.append(
                        {
                            "name": "Randomly select step_hosts",
                            "shell": "%s > /tmp/step_hosts" % any_host,
                            "delegate_to": "localhost",
                            "run_once": True,
                        }
                    )

                    tasks.append(
                        {
                            "set_fact": {
                                "step_hosts": "{{ lookup('lines', 'cat /tmp/step_hosts') }}",
                            },
                        }
                    )
                else:
                    t["vars"]["step_hosts"] = ["{{ %s }}" % h for h in hosts]

                t["when"].append("inventory_hostname in step_hosts")

            for k in ["vars", "when"]:
                if not t[k]:
                    del t[k]

            tasks.append(t)

        return tasks

    def find_custom_step(self, step):
        """
        Given an entry under steps that does not correspond to any built-in
        step, this functions looks for a custom step definition file under each
        of the directories specified with ``--steps-from`` (ignoring those that
        do not exist). If it finds one, it returns an include task to include
        the step, otherwise it returns None.
        """
        # - step: somename
        #   args:
        #     key: value
        #     key: value
        #   other: settings
        #   …
        # - somename:
        #     key: value
        #     key: value
        #   other: settings
        potential_step_names = []
        if "step" in step and "args" in step:
            potential_step_names.append(step["step"])
        else:
            exclude_keys = ["hosts"]
            potential_step_names = [
                s
                for s in step.keys()
                if s not in exclude_keys
                and (isinstance(step[s], dict) or step[s] is None)
            ]

        step_directories = self.options.get("step_directories", [])
        step_directories = [s for s in step_directories if os.path.exists(s)]

        s = None
        for k in potential_step_names:
            for directory in step_directories:
                f = os.path.join(directory, "%s.yml" % k)
                if os.path.exists(f):
                    _vars = {}
                    _vars.update(step)
                    if "args" not in _vars:
                        step_args = {}
                        if k in step and isinstance(step[k], dict):
                            step_args = step[k]
                        _vars["args"] = step_args
                    s = {
                        "include_tasks": {"file": f},
                        "vars": _vars,
                    }
                    break

        return s


def read_yaml(infile):
    """
    Parses the contents of the given input file as YAML and returns the
    resulting data structure.
    """
    with open(infile, "r") as input_fh:
        return yaml.load(input_fh, Loader=yaml.FullLoader)


def write_yaml(outdir, filename, data):
    """
    Given an output directory, a filename, and a data structure, creates the
    output file and writes the data structure to it in YAML format.
    """
    with open(os.path.join(outdir, filename), "w") as f:
        yaml.dump(
            data, f, explicit_start=True, default_flow_style=False, sort_keys=True
        )


def random_string(length):
    """
    Returns a random string of the given length
    """
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
