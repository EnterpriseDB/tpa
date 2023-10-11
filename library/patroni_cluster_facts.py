#!/usr/bin/python
# -*- coding: utf-8 -*-

#  © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.
#
from __future__ import absolute_import, division, print_function

import json
import os.path
from subprocess import Popen, PIPE
from threading import Timer

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r"""
---
module: patroni_cluster_facts
short_description: Gather facts for a patroni cluster
description:
  - This mainly deals with the state of the cluster pre-init
    and details retrieved from the DCS using patronictl.
    Once the cluster is running API endpoints report better
    info, e.g. http://localhost:8008/patroni
version_added: "2.9"
options:
 cluster:
   description:
     - Name of the patroni cluster to collect facts from
   required: false
   default: "patroni"
 config_dir:
   description:
     - Path to the directory containing patroni cluster configuration files
   required: false
   default: "/etc/patroni"
 patronictl_path:
   description:
     - Path to the patronictl script
   required: false
   default: "/usr/bin/patronictl"
author: "Matt Baker <matt.baker@enterprisedb.com>"
"""

EXAMPLES = r"""
- name: Get patroni status
  patroni_cluster_facts:
    cluster: "{{ cluster_name }}"
    config_dir: "{{ patroni_etc }}"
    patronictl_path: "{{ patronictl_path }}"
"""

RETURN = r"""
patroni_cluster:
   description: Information about any discovered patroni cluster.
   returned: always
   type: dict
   contains:
     config:
       description: Path to the patroni cluster configuration file
       returned: always
       type: str
       sample: /etc/patroni/patroni.yml
     initialised:
       description: Boolean value as a string of whether the cluster DCS info is populated for the cluster
       returned: always
       type: str
     members:
       description: Output from patronictl list command for the cluster
       returned: always
       type: list
       sample:
           - {"Cluster": "patroni",
              "Member": "pat1",
              "Host": "pat1:5444",
              "Role": "Leader",
              "State": "running",
              "TL": 3,
              "Pending restart": "*"}
           - ...
patroni_version:
   description:
   returned: always
   type:
"""


def run(cmd, timeout=10):
    """Run a system command with a timeout."""
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    timer = Timer(timeout, proc.kill)
    try:
        timer.start()
        stdout, stderr = proc.communicate()
        ret = proc.returncode
        return stdout.decode(), stderr.decode(), ret
    finally:
        timer.cancel()


class PatroniCluster(object):
    def __init__(self, name, config_dir, patronictl_path, locale):
        self.name = name
        self.config_dir = config_dir
        self.patronictl_path = patronictl_path
        self.locale = locale
        self._init = "no"
        self._status = []

    def _patronictl(self, *args):
        if not os.path.exists(self.patronictl_path):
            return (
                "",
                "Path to patronictl does not exist: {path}".format(
                    path=self.patronictl_path
                ),
                127,
            )
        os.environ["LANG"] = self.locale
        os.environ["LC_ALL"] = self.locale
        command = [self.patronictl_path] + list(args)
        return run(command)

    @property
    def config(self):
        """Get the patroni cluster configuration."""
        return "{conf}/{name}.yml".format(conf=self.config_dir, name=self.name)

    @property
    def init(self):
        """Has the Patroni cluster config been initialised."""
        if self.status and all(
            True for node in self.status if node.get("Cluster", False) == self.name
        ):
            self._init = "yes"
        elif os.path.exists(self.config):
            self._init = "present"
        return self._init

    @property
    def installed(self):
        """Get the installed version of patroni."""
        stdout, stderr, ret = self._patronictl("version")
        if ret:
            result = str(stderr)
        else:
            try:
                result = stdout.split()[2]
            except IndexError:
                result = "No version found in output of: patronictl version"
        return result

    @property
    def status(self):
        if not self._status:
            self._status = self.get_status()
        return self._status

    def get_status(self):
        """Get the patroni cluster status."""
        result = []
        if not os.path.exists(self.config) or self.installed is False:
            return result
        stdout, stderr, ret = self._patronictl("-c", self.config, "list", "-f", "json")
        if ret:
            # warning here? Raise?
            return result
        else:
            try:
                result = json.loads(stdout)
            except json.JSONDecodeError:
                # warning here? Raise?
                return result
        return result


def run_module():  # pragma: nocover
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        cluster=dict(type="str", required=True),
        config_dir=dict(type="str", required=False, default="/etc/patroni"),
        patronictl_path=dict(type="str", required=False, default="/usr/bin/patronictl"),
        locale=dict(type="str", required=False, default="C.UTF-8"),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        ansible_facts=dict(
            patroni_cluster=dict(config="", initialised="no", members=[]),
            patroni_version="",
        ),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    cluster = PatroniCluster(
        name=module.params["cluster"],
        config_dir=module.params["config_dir"],
        patronictl_path=module.params["patronictl_path"],
        locale=module.params["locale"],
    )
    result["ansible_facts"] = dict(
        patroni_cluster=dict(
            config=cluster.config, initialised=cluster.init, members=cluster.status
        ),
        patroni_version=cluster.installed,
    )

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    # if module.params["name"] == "fail me":
    #     module.fail_json(msg="You requested this to fail", **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():  # pragma: nocover
    run_module()


if __name__ == "__main__":  # pragma: nocover
    main()
