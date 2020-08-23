# Filesystem configuration

TPAexec allows you to define a list of `volumes` attached to each
instance.

This list comprises both platform-specific settings that are used during
provisioning and filesystem-level settings used during deployment.

First, `tpaexec provision` will use the information to create and
attach volumes to the instance (if applicable; see platform-specific
sections below for details). Then it will write a simplified list of
volumes (containing only non-platform-specific settings) as a host var
for the instance. Finally, `tpaexec deploy` will act on the simplified
list to set up and mount filesystems, if required.

Here's a moderately complex example from an AWS cluster:

```yaml
instances:
- Name: one
  …
  volumes:
  - device_name: root
    volume_type: gp2
    volume_size: 32
  - raid_device: /dev/md0
    device_name: /dev/xvdf
    volume_type: io2
    volume_size: 64
    raid_units: 2
    raid_level: 1
    iops: 5000
    vars:
      volume_for: postgres_data
      encryption: luks
  - raid_device: /dev/md1
    device_name: /dev/xvdh
    ephemeral: ephemeral0
    raid_units: all
    vars:
      mountpoint: /mnt/scratch
```

In this example, the EC2 instance will end up with a 32GB EBS root
volume, a 64GB RAID-1 volume comprising two provisioned-iops EBS volumes
mounted as /opt/postgres/data, and a /tmp/scratch filesystem comprising
all available instance-store (“ephemeral”) volumes, whose number and
size are determined by the instance type.

The details are documented in the section on AWS below, but settings
like `volume_type` and `volume_size` are used during provisioning, while
settings under `vars` like `volume_for` or `mountpoint` are written to
the inventory for use during deployment.

## default_volumes

Volumes are properties of an instance. You cannot set them in
`cluster_vars`, because they contain platform-specific settings.

The
[`instance_defaults`](configure-cluster.md#instance_defaults)
mechanism makes special allowances for volume definitions. Since volume
definitions in a large cluster may be quite repetitive (especially since
we recommend that instances in a cluster be configured as close to each
other as possible, you can specify `default_volumes` as shown here:

```yaml
instance_defaults:
  default_volumes:
  - device_name: root
    volume_type: gp2
    volume_size: 32
  - device_name: /dev/xvdf
    volume_size: 100

instances:
- Name: one
  …
- Name: two
  volumes:
  - device_name: /dev/xvdf
    volume_size: 64
  - device_name: /dev/xvdg
    volume_size: 64
    …
- Name: three
  volumes:
  - device_name: /dev/xvdf
    volume_type: none
- Name: four
  volumes: []
```

Here every instance will have a 32GB root volume and a 100GB additional
volume by default (as is the case for instance `one`, which does not
specify anything different). Instance `two` will have the same root
volume, but it overrides `/dev/xvdf` to be 64GB instead, and has another
64GB volume in addition. Instance `three` will have the same root
volume, but no additional volume because it sets `volume_type: none` for
the default `/dev/xvdf`. Instance `four` will have no volumes at all.

An instance starts off with whatever is specified in `default_volumes`,
and its `volumes` entries can override a default entry with the same
`device_name`, remove a volume by setting `volume_type` to `none`, add
new volumes with different names, or reject the defaults altogether.

(This behaviour of merging two lists is specific to `default_volumes`.
If you set any other list in both `instance_defaults` and `instances`,
the latter will override the former completely.)

## Platform AWS

On AWS EC2 instances, you can attach EBS volumes.

```yaml
instances:
- Name: one
  …
  volumes:
  - device_name: root
    volume_type: gp2
    volume_size: 32
    encrypted: yes
    …
  - device_name: /dev/xvdf
    volume_type: io1
    volume_size: 32
    iops: 10000
    delete_on_termination: false
    …
  - device_name: /dev/xvdg
    ephemeral: ephemeral0
    …
```

TPAexec translates a `device_name` of `root` to `/dev/sda` or
`/dev/xvda` based on the instance type, so that you don't need to
remember (or change) which one to use.

The `volume_type` specifies the EBS volume type, e.g., `gp2` (for
“general-purpose” EBS volumes), `io1` for provisioned-IOPS volumes (in
which case you must also set `iops: 5000`), etc.

The `volume_size` specifies the size of the volume in gigabytes.

Set `encrypted: yes` to enable EBS encryption at rest. (This is an AWS
feature, enabled by default in newly-generated TPAexec configurations,
and is different from [LUKS encryption](#luks-encryption), explained
below.)

Set `delete_on_termination` to `false` to prevent the volume from being
destroyed when the attached instance is terminated (which is the default
behaviour).

Set `ephemeral: ephemeralN` to use a physically-attached
[instance store volume](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html),
formerly known as an ephemeral volume. The number, type, and size of
available instance store volumes depends on the instance type. Not all
instances have instance store volumes. Use instance store volumes only
for testing or temporary data, and EBS volumes for any data that you
care about.

For an EBS volume, you can also set `snapshot: snap-xxxxxxxx` to attach
a volume from an existing snapshot. Volumes restored from snapshots may
be extraordinarily slow until enough data has been read from S3 and
cached locally. (In particular, you can spin up a new instance with
`PGDATA` from a snapshot, but expect it to take several hours before it
is ready to handle your full load.)

If you set `attach_existing: yes` for a volume, and there is an existing
unattached EBS volume with matching Name/type/size/iops, a new volume
will not be created when launching the instance, but instead the
existing one will be attached to the instance the first time it starts.
Reattached EBS volumes do not suffer from the performance limitations of
volumes created from snapshots.

## Platform bare

TPAexec has no control over what volumes may be attached to
pre-provisioned `bare` instances, but if you define `volumes` with the
appropriate `device_name`, it will handle `mkfs` and `mount` for the
devices if required.

## Platform Docker

Docker containers can have attached volumes, but they are bind-mounted
directories, not regular block devices. They do not need to be
separately initialised or mounted. As such, the configuration looks
quite different.

```yaml
instances:
- Name: one
  platform: docker
  …
  volumes:
  - /host/path/to/dir:/tmp/container/path:ro
  - named_volume:/mnt/somevol:rw
```

You may recognise these volume specifications as arguments to
`docker run -v`.

The volumes are attached when the container is created, and there are no
further actions during deployment.

## RAID arrays

On AWS EC2 instances, you can define RAID volumes:

```yaml
instances:
- Name: one
  …
  volumes:
  - raid_device: /dev/md0
    device_name: /dev/xvdf
    raid_units: 2
    raid_level: 1
    volume_type: gp2
    volume_size: 100
    vars:
      volume_for: postgres_data
```

This example will attach 4×100GB EBS gp2 volumes (`/dev/xvd[f-i]`) and
assemble them into a RAID-1 volume named `/dev/md0`. The handling of
`volume_for` or `mountpoint` during deployment happens as with any other
volume.

TPAexec does not currently support the creation and assembly of RAID
arrays on other platforms, but you can use an existing array by adding
an entry to volumes with `device_name: /dev/md0` or `/dev/mapper/xyz`.
TPAexec will handle `mkfs` and `mount` as with any other block device.

## LUKS encryption

TPAexec can set up a LUKS-encrypted device:

```yaml
instances:
- Name: one
  …
  volumes:
  - device_name: /dev/xyz
    vars:
      encryption: luks
      luks_device: mappedname
      volume_for: …
```

If a volume with `encryption: luks` set is not already initialised,
TPAexec will use `cryptsetup` to first `luksFormat` and then `luksOpen`
it to map it under `/dev/mapper/mappedname` before handling filesystem
creation as with any other device.

If you create a LUKS-encrypted `volume_for: postgres_data`, TPAexec will
configure Postgres to not start automatically at boot. You can use
`tpaexec start-postgres clustername` to mount the volume and start
Postgres (and `stop-postgres` to stop Postgres and unmap the volume).

The LUKS passphrase is generated locally and stored in the vault.

## Filesystem creation and mounting

If any `device` does not contain a valid filesystem, it will be
initialised with `mkfs`.

```yaml
instances:
- Name: one
  …
  volumes:
  - device_name: /dev/xyz
    vars:
      volume_for: …
      fstype: ext4
      fsopts:
        - -cc
        - -m 2
      mountopts: 'defaults,relatime,nosuid'
      readahead: 65536
      owner: root
      group: root
      mode: 0755
```

You can specify the `fstype` (default: ext4), `fsopts` to be passed to
mkfs (default: none), and `mountopts` to be passed to mount and written
to fstab (see below).

TPAexec will set the readahead for the device to 16MB by default (and
make the value persist across reboots), but you can specify a different
value for the volume as shown above.

There are two ways to determine where a volume is mounted. You can
either specify a `mountpoint` explicitly, or you can set `volume_for` to
`postgres_data` or `barman_data`, and TPAexec will translate the setting
into an appropriate mountpoint for the system.

Once the `mountpoint` is determined, the `device` will be mounted there
with the given `mountopts` (default: `defaults,noatime`). An entry will
also be created for the filesystem in `/etc/fstab`.

You may optionally specify `owner`, `group`, or `mode` for the volume,
and these attributes will be set on the `mountpoint`. Remember that at
this very early stage of deployment, you cannot count on the `postgres`
user to exist. In any case, TPAexec will (separately) ensure that any
directories needed by Postgres have the right ownership and permissions,
so you don't have to do it yourself.
