#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: ec2_instance_status
short_description: Return DescribeInstanceResults for a single EC2 instance
description:
   - Issue a DescribeInstanceStatus request for a single instance and return the
     (first/only) resulting "InstanceStatuses".
version_added: "2.4"
options:
  instance_id:
    description:
      - The instance id (i-xxx) of the instance to query.
    required: true
notes:
   - This module requires the I(boto3) Python library to be installed.
requirements: [ boto3 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- ec2_instance_status: instance_id=i-xxx
  register: i
'''

import traceback

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict,
                                      get_aws_connection_info)

def get_instance_status(module, client):
    """
    Given a single instance_id, issue DescribeInstanceStatus and return the
    results.

    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstanceStatus.html

    The results are described in the following links:

    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceStatus.html
    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceStatusSummary.html
    http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceStatusDetails.html
    """

    instance_id = module.params.get('instance_id')

    status = {'failed': True}
    try:
        ret = client.describe_instance_status(InstanceIds=[instance_id])
        status['results'] = ret
        if 'InstanceStatuses' in ret:
            ret = ret['InstanceStatuses']
            status['request_status'] = 'unknown'
            if len(ret) == 1:
                status = camel_dict_to_snake_dict(ret[0])
                status['request_status'] = 'ok'

                # InstanceStatusSummary.status may be 'ok', 'impaired',
                # 'insufficient-data', 'not-applicable', or 'initializing'.

                if status['instance_status']['status'] == 'impaired' or \
                    status['system_status']['status'] == 'impaired':
                    status['failed'] = True

                # InstanceStatusDetails.status may be 'passed', 'failed',
                # 'insufficient-data', or 'initializing'.

                for i in status['instance_status']['details'] + \
                    status['system_status']['details']:
                    if i['status'] == 'failed':
                        status['failed'] = True
                        break

    except (botocore.exceptions.ClientError) as e:
        module.fail_json(msg=e.response['Error']['Message'], exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    return status

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance_id=dict(required=True)
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=HAS_BOTO3)

    if not region:
        module.fail_json(msg="AWS region must be specified (e.g., eu-west-1)")

    try:
        client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ProfileNotFound) as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    module.exit_json(**get_instance_status(module, client))

if __name__ == '__main__':
    main()
