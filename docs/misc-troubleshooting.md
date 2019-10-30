# Troubleshooting

### Recreate python virtualenv

Occasionally the python virtualenv can get in an inconsistent state, in which case the easiest solution is to delete and recreate it. Symptoms of a broken virtualenv can include errors during provisioning like:

```
TASK [Write Vagrantfile and firstboot.sh] ******************************************************************************************************************************
failed: [localhost] (item=Vagrantfile) => {"changed": false, "checksum": "bf1403a17d897b68fa8137784d298d4da36fb7f9", "item": "Vagrantfile", "msg": "Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!"}
```

To create a new virtualenv (assuming tpaexec was installed into the default location):

```
[tpa]$ sudo rm -rf /opt/2ndQuadrant/TPA/tpa-virtualenv
[tpa]$ sudo /opt/2ndQuadrant/TPA/bin/tpaexec setup
```

###Strange AWS errors regarding credentials
If the time & date of the TPAexec server isn't correct, you can get AWS errors similar to this during provisioning:
```
TASK [Register key tpa_cluster in each region] **********************************************
An exception occurred during task execution. To see the full traceback, use -vvv. The error was: ClientError: An error occurred (AuthFailure) when calling the DescribeKeyPairs operation: AWS was not able to validate the provided access credentials
failed: [localhost] (item=eu-central-1) => {"boto3_version": "1.8.8", "botocore_version": "1.11.8", "changed": false, "error": {"code": "AuthFailure", "message": "AWS was not able to validate the provided access credentials"}, "item": "eu-central-1", "msg": "error finding keypair: An error occurred (AuthFailure) when calling the DescribeKeyPairs operation: AWS was not able to validate the provided access credentials", "response_metadata": {"http_headers": {"date": "Thu, 27 Sep 2018 12:49:41 GMT", "server": "AmazonEC2", "transfer-encoding": "chunked"}, "http_status_code": 401, "request_id": "a0d905ba-188f-48fe-8e5a-c8d8799e3232", "retry_attempts": 0}}

```

Solution - set the time and date correctly.

```
[tpa]$ sudo ntpdate pool.ntp.org
```

### Logging

By default, all tpaexec logging will be saved in logfile `<clusterdir>/ansible.log`

To change the logfile location, set environment variable `ANSIBLE_LOG_PATH` to the desired location - e.g.

```
export ANSIBLE_LOG_PATH=~/ansible.log
```

To increase the verbosity of logging, just add `-v`/`-vv`/`-vvv`/`-vvvv`/`-vvvvv` to tpaexec command line:

```
[tpa]$ tpaexec deploy <clustername> -v

-v     shows the results of modules
-vv    shows the files from which tasks come
-vvv   shows what commands are being executed on the target machines
-vvvv  enables connection debugging, what callbacks have been loaded
-vvvvv shows some additional ssh configuration, filepath information
```

### Cluster test

An easy way to smoketest an existing cluster is to run:

```
[tpa]$ tpaexec test <clustername>
```

This will do a functional test of the cluster components, followed by a performance test of the cluster, using pgbench. As pgbench can take a while to complete, benchmarking can be omitted by running:

```
[tpa]$ tpaexec test <clustername> --skip-tags pgbench
```

Tags in the test role are `repmgr,postgres,barman,pgbench`

Note that when specifying multiple tags, they should be comma delimited, with
no spaces; for example: 

```
[tpa]$ tpaexec test <clustername> --skip-tags barman,pgbench
```

### TPAexec server test

To check the installation of the TPAexec server itself, run:

```
[tpa]$ tpaexec selftest
```

### Skipping or including specific tags

When re-running a tpaexec provision or deploy after a failure, in the interests
of time, it can sometimes be useful to miss out tasks by skipping specific tags.
For example to miss out the repmgr tasks:

```
[tpa]$ tpaexec deploy <clustername> --skip-tags repmgr
```

To jump straight to re-run a particular task by specifying a tag--for example,
to immediately run BDR tasks:

```
[tpa]$ tpaexec deploy <bdr-clustername> --tags bdr
```

*Note that this assumes that the previous tasks all completed successfully.*


To find all the tags for the relevant architecture that might be useful, run:

```
[tpa]$ grep -rs "tags:" /opt/2ndQuadrant/TPA/architectures
```
