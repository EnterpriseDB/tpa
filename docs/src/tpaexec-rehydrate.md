# tpaexec rehydrate

The `tpaexec rehydrate` command rebuilds AWS EC2 instances with an
updated machine image (AMI), and allows for the rapid deployment of
security patches and OS upgrades to a cluster managed by TPAexec.

Given a new AMI with all the required changes, this command terminates
an instance, replaces it with a newly-provisioned instance that uses the
new image, and attaches the data volumes from the old instance before
recreating the configuration of the server exactly (based on
`config.yml`).

Publishing up-to-date images and requiring servers to be rebuilt from
scratch on a regular schedule is an alternative to allowing a fleet of
servers to download and install individual security updates themselves.
It makes it simpler to track the state of each server at a glance, and
discourages any manual changes to individual servers (they would be
wiped out during the instance replacement).

TPAexec makes it simple to minimise disruption to the cluster as a whole
during the rehydration, even though the process must necessarily involve
downtime for individual servers as they are terminated and replaced. On
a [streaming replication cluster](architecture-M1.md), you can rehydrate
the replicas first, then use [`tpaexec switchover`](tpaexec-switchover.md)
to convert the primary to a replica before rehydrating it. On
[BDR-Always-ON clusters](architecture-BDR-Always-ON.md), you can [remove
each server from the haproxy server pool](tpaexec-server-pool.md) before
rehydrating it, then add it back afterwards.

If you just want to install minor-version updates to Postgres and
associated components, you can use the
[`tpaexec update-postgres`](tpaexec-update-postgres.md) command instead.

## Prerequisites

To be able to rehydrate an instance, you must specify
`delete_on_termination: no` and `attach_existing: yes` for each of its
data volumes in `config.yml`. (The new instance will necessarily have a
new EBS root volume.)

By default, when you terminate an EC2 instance, the EBS volumes attached
to it are also terminated. In this case, since we want to reattach them
to a new instance, we must disable `delete_on_termination`. Setting
`attach_existing` makes TPAexec search for old volumes when provisioning
a new instance and, if found, attach them to the instance after it's
running.

Do not stop or terminate the old instance manually; the
`tpaexec rehydrate` command will do this after verifying that the
instance can be safely rehydrated.

## Example

Let's assume you have an AWS cluster configuration in `~/clusters/night`.

### Change the configuration

First, you must edit `config.yml` and specify the new AMI. For example:

```yaml
ec2_ami:
  Name: RHEL-8.3_HVM-20210209-x86_64-0-Hourly2-GP2
  Owner: '309956199498'
```

Check that `delete_on_termination` is disabled for each data volume. If
the parameter is not present, you can check its value through the AWS
EC2 management console. Click on 'Instances', select an instance, then
open the 'Description' tab and scroll down to 'Block devices', and click
on an EBS volume. If the "Delete on termination" flag is set to true,
you can [change it using `awscli`](#appendix). Also check
`attach_existing` and set it to `yes` if it isn't set already.

Here's an example with both attributes correctly set:

```yaml
instances:
- node: 1
  Name: vlad
  subnet: 10.33.14.0/24
  role: primary
  volumes:
  - device_name: /dev/xvdf
    volume_type: gp2
    volume_size: 16
    attach_existing: yes
    delete_on_termination: false
    vars:
      volume_for: postgres_data
      mountpoint: /var/lib/pgsql
```

(Note that volume parameters may be set in `instance_defaults` as well
as under specific instances. Search for `volumes:` and make sure all of
the relevant volumes have these two attributes set.)

### Start the rehydration

Here's the syntax for the rehydrate command:

```bash
$ tpaexec rehydrate ~/clusters/night instancename
```

You can specify a single instance name or a comma-separated list of
instance names (but you cannot rehydrate all of the instances in the
cluster at once).

The command will first check that every non-root EBS volume attached to
the instance (or instances) being rehydrated has the
`delete_on_termination` flag set to false. If this is not the case, it
will stop with an error before any instance is terminated.

If the volume attributes are set correctly, the command will first
terminate each of the instances, then run provision and deploy to
replace them with new instances using the new AMI.

## Rehydrate in phases

In order to maintain cluster continuity, we recommend rehydrating the
cluster in phases.

For example, in a [cluster that uses streaming
replication](architecture-M1.md) with a primary instance, two replicas,
and a Barman backup server, you could rehydrate the Barman instance and
one replica first, then another replica, then
[switchover](tpaexec-switchover.md) from the primary to one of the
rehydrated replicas, rehydrate the former primary, and (optionally),
switchover back to the original primary. This sequence ensures that one
primary and one replica are always available.

## Appendix

#### Using awscli to change volume attributes

First, find the instance and EBS volume in the AWS management console.
Click on 'Instances', select an instance, open the 'Description' tab and
scroll down to 'Block devices', and select an EBS volume. To disable
`delete_on_termination`, run the following command after substituting
the correct values for the `--region`, `--instance-id`, and block device
name:

```bash
$ aws ec2 modify-instance-attribute \
    --region eu-west-1 --instance-id i-XXXXXXXXXXXXXXXXX \
    --block-device-mappings \
      '[{"DeviceName": "/dev/xvdf", "Ebs": {"DeleteOnTermination": false}}]'
```

Do this for each of the data volumes for the instance, and after a brief
delay, you should be able to see the changes in the management console,
and `tpaexec rehydrate` will also detect that the instance can be safely
rehydrated.
