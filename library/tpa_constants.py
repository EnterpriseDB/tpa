#!/usr/bin/python
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

# This is a wrapper Ansible module to expose TPA library constants.

import sys
import os

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from ansible.module_utils.basic import AnsibleModule
from tpa import constants as tpa_constants


def main():
    argument_spect = {"name": {"type": "str", "required": False, "default": None}}
    module = AnsibleModule(argument_spec=argument_spect, supports_check_mode=True)

    name = module.params.get("name")
    result = {"changed": False}

    if name:
        constant_value = getattr(tpa_constants, name, None)
        if constant_value is None:
            module.fail_json(msg=f"Unknown constant: {name}")
        result[name.lower()] = constant_value
    else:
        for final_constant in tpa_constants.__annotations__:
            result[final_constant.lower()] = getattr(tpa_constants, final_constant)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
