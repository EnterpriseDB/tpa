Cluster configuration
=====================

The ``tpaexec configure`` command generates a YAML cluster configuration
file that is required by subsequent stages in the provision/deploy/test
cycle.

## Quickstart

```
[tpa]$ tpaexec configure ~/clusters/speedy --architecture M1
```

This command will create a directory named ``~/clusters/speedy`` and
generate a configuration file named ``config.yml`` that follows the
layout of the architecture named M1 (single primary, N replicas).

The command accepts a number of options (some common, some specific to
the selected architecture or platform) to modify the generated
configuration, but the defaults are sensible and intended to be usable
for testing straightaway. You may edit the generated config.yml to
fine-tune the configuration.

(We recommend that you keep all your cluster configurations in a common
directory, e.g., ``~/clusters`` in the example above.)

### Current configuration options

```
tpaexec configure <clustername> --architecture <arch> --platform <platform> 
--region <region> --[subnet <CIDR> | --subnet-pattern <pattern>] 
--instance-type <instance type> [--distribution [RedHat|Debian|Ubuntu] 
--minimal | --os [Debian-minimal|RedHat-minimal|Ubuntu-minimal]] 
--postgres-version [10|9.6] --postgres-package-version <ver>
--repmgr-package-version <ver> --barman-package-version <ver>
--pglogical-package-version <ver> --bdr-package-version <ver>
--pgbouncer-package-version <ver>
--hostnames-from <filename> --hostnames-pattern <pattern>
```

```
<clustername> - directory name to be created for the cluster. Examples:
~/tpa/clusters/speedy
./speedy
/home/tpa/tpa/clusters/speedy
```
The currently supported options can be found by running `tpaexec help configure-options`.

### Architecture options

```
--architecture <arch> - M1|BDR-Always-ON|Training
M1: Postgres with streaming replication (M1 is single master - one primary, n replicas).
BDR-Always-ON: Bi Directional Replication in an Always-ON configuration 
   (2ndQuadrant internal use only, still in development, and requires access 
to internal repositories)
Training: Creates clusters for 2ndQuadrant training sessions (Designed for
   2ndQuadrant use; unsupported)
```
The currently available architectures can be found by running `tpaexec info architectures`.
### Platform options

```
--platform <platform> - bare|aws|lxd
bare: Servers accessible via SSH (e.g., bare metal, or already-provisioned 
   servers on any cloud provider).
aws: AWS EC2 instances (This is the default, if --platform not present)
lxd: lxd containers (Unsupported; still in development)
```

```
--region <region> - AWS region (Defaults to eu-west-1). 
* Specific to --platform aws
```

```
--instance-type <instance type> - AWS instance type (Defaults to t2.micro). 
* Specific to --platform aws
```
### Subnet selection

```
--subnet <CIDR> - By default, each cluster is assigned a random /28 subnet 
   under 10.33/16, but depending on the architecture, there may be one or more 
   subnets, and each subnet may be anywhere between a /24 and a /29.
```

```
--subnet-pattern <pattern> - You may instead specify --subnet-pattern 192.0.x.x 
   to generate random subnets (as many as required by the architecture) matching 
   the given pattern.
```
### Distribution

```
--distribution [RedHat|Debian|Ubuntu] (Defaults to Debian)
```

```
--minimal - Use the stock distribution images instead of TPA images that have 
   Postgres and other software preinstalled.
```

```
--os [RedHat-minimal|Debian-minimal|Ubuntu-minimal] - this option can be used 
   instead of the previous 2 options (--distribution and --minimal)
```
### Software versions

By default, we always install the latest version of every package. This is usually 
the desired behaviour, but in some testing scenarios, it may be necessary to 
select specific package versions.

```
--postgres-version [10|9.6] - 10 is the default, 9.6 is also supported. 
   Versions 9.4 and 9.5 are no longer actively maintained.
```

```
--postgres-package-version <pkg> - Specific postgres package, e.g. 10.4-2.pgdg90+1
--repmgr-package-version <pkg> - Specific repmgr package, e.g. 4.0.5-1.pgdg90+1
--barman-package-version <pkg> - Specific barman package, e.g. 2.4-1.pgdg90+1
--pgbouncer-package-version <pkg> - Specific pgbouncer package, e.g. '1.8*'
--pglogical-package-version <pkg> - Specific pglogical package, e.g. '2.2.0*'
--bdr-package-version <pkg> - Specific bdr package, e.g. '3.0.2*'
```
### Hostnames

By default, ``tpaexec configure`` will randomly select as many hostnames
as it needs from a pre-approved list of several dozen names. This should
be enough for most clusters.

```
--hostnames-from <filename> - select names from a different list 
   (e.g., if you need more names than are available in the canned list). 
   The file must contain one hostname per line.
```
```
--hostnames-pattern <pattern> - restrict hostnames to those matching 
   the egrep-syntax pattern. If you choose to do this, you must ensure that 
   the pattern matches only valid hostnames (``[a-zA-Z0-9-]``) and that it 
   finds a sufficient number thereof.
```

------

### Example

```
tpaexec configure ~/tpa/clusters/speedy --architecture M1
```

This will create config files that can be used to provision and deploy a 4 node M1 AWS cluster in AWS region `eu-west-1`, with each node of type `t2.micro`. The AMIs have defaulted to `TPA-Debian-PGDG-10-2018*`

```
[tpa]$ ls ~/tpa/clusters/speedy3
config.yml  deploy.yml
[tpa]$ head -35 ~/tpa/clusters/speedy3/config.yml
---
architecture: M1

cluster_name: speedy3

ec2_ami:
  Name: TPA-Debian-PGDG-10-2018*
  Owner: self

ec2_vpc:
  Name: Test

cluster_vars:
  vpn_network: 192.168.33.0/24

instance_defaults:
    type: t2.micro
    region: eu-west-1
    subnet: 10.33.217.224/28
    vars:
      ansible_user: admin

instances:
  - node: 1
    Name: quanta
    volumes:
        - raid_device: /dev/md0
          device_name: /dev/xvdb
          volume_type: gp2
          volume_size: 16
          raid_units: 2
          vars:
            volume_for: postgres_data
    role: primary

```

It's possible to write config.yml entirely by hand, but it's much
easier to edit a generate file to fine-tune the configuration.
