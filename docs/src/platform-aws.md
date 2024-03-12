# aws

TPA fully supports provisioning production clusters on AWS EC2.

## API access setup

To use the AWS API, you must:

* [Obtain an access keypair](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
* [Add it to your configuration](https://boto.readthedocs.org/en/latest/boto_config_tut.html)

For example:

```bash
[tpa]$ cat > ~/.aws/credentials
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

The AMI user must have at least the following set of permissions so tpaexec
can use it to provision ec2 resources:
```
ec2:AssociateRouteTable
ec2:AttachInternetGateway
ec2:AuthorizeSecurityGroupIngress
ec2:CreateInternetGateway
ec2:CreateRoute
ec2:CreateRouteTable
ec2:CreateSecurityGroup
ec2:CreateSubnet
ec2:CreateTags
ec2:CreateVpc
ec2:DeleteKeyPair
ec2:DeleteRouteTable
ec2:DeleteSecurityGroup
ec2:DeleteSubnet
ec2:DeleteVpc
ec2:DescribeImages
ec2:DescribeInstanceStatus
ec2:DescribeInstances
ec2:DescribeInternetGateways
ec2:DescribeKeyPairs
ec2:DescribeRouteTables
ec2:DescribeSecurityGroups
ec2:DescribeSubnets
ec2:DescribeTags
ec2:DescribeVolumes
ec2:DescribeVpcAttribute
ec2:DescribeVpcClassicLink
ec2:DescribeVpcClassicLinkDnsSupport
ec2:DescribeVpcs
ec2:DisassociateRouteTable
ec2:ImportKeyPair
ec2:ModifyVpcAttribute
ec2:RevokeSecurityGroupIngress
ec2:RunInstances
ec2:TerminateInstances
iam:AddRoleToInstanceProfile
iam:CreateInstanceProfile
iam:CreateRole
iam:DeleteInstanceProfile
iam:DeleteRole
iam:DeleteRolePolicy
iam:GetInstanceProfile
iam:GetRole
iam:GetRolePolicy
iam:ListAttachedRolePolicies
iam:ListGroups
iam:ListInstanceProfiles
iam:ListInstanceProfilesForRole
iam:ListRolePolicies
iam:ListRoles
iam:ListUsers
iam:PassRole
iam:PutRolePolicy
iam:RemoveRoleFromInstanceProfile
kms:CreateGrant
kms:GenerateDataKeyWithoutPlaintext
s3:CreateBucket
s3:GetBucketVersioning
s3:GetObject
s3:GetObjectTagging
s3:ListAllMyBuckets
s3:ListBucket
s3:ListBucketVersions
s3:PutBucketOwnershipControls
s3:PutObject
s3:PutObjectAcl
```

## Introduction

The service is physically subdivided into
[regions and availability zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html).
An availability zone is represented by a region code followed by a
single letter, for example, eu-west-1a. (But that name can refer to different
locations for different AWS accounts, and there's no way to coordinate
the interpretation between accounts.)

AWS regions are completely isolated from each other and share no
resources. Availability zones within a region are physically separated,
and logically mostly isolated, but are connected by low-latency links
and can share certain networking resources.

### Networking

All networking configuration in AWS happens in the context of a
[virtual private cloud](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-vpc.html)
within a region. Within a VPC, you can create
[subnets](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Subnets.html)
that are tied to a specific availability zone, along with internet
gateways, routing tables, and so on.

You can create any number of
[security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html#vpc-security-groups)
to configure rules for the inbound and outbound traffic that's permitted to
instances (in terms of protocol, a destination port range, and a source
or destination IP address range).

### Instances

AWS EC2 offers a variety of
[instance types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html)
with different hardware configurations at different
price/performance points. Within a subnet in a particular availability
zone, you can create
[EC2 instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Instances.html)
based on a distribution image known as an
[AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html),
and attach one or more
[EBS volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html)
to provide persistent storage to the instance. You can SSH to the
instances by registering an
[SSH public key](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).

Instances are always assigned a private IP address within their subnet.
Depending on the subnet configuration, they might also be assigned an
[ephemeral public IP address](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#concepts-public-addresses),
which is lost when the instance is shut down, and a different ephemeral
IP is assigned when it's started again. You can instead assign a
static region-specific, routable IP address known as an
[elastic IP](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)
to any instance.

For an instance to be reachable from the outside world, it must not only
have a routable IP address, but the VPC's networking configuration
(internet gateway, routing tables, security groups) must also align to
permit access.

## Configuration

Here's a brief description of the AWS-specific settings that you can
specify using `tpaexec configure` or define directly in `config.yml`.

### Regions

You can specify one or more regions for the cluster to use with `--region` or
`--regions`. TPA generates the required VPC entries associated with each of
them and distributes locations into these regions evenly by using different
availability zones while possible.

`regions` are different from `locations`. Each location belongs to a region
and an availability zone inside this region. `regions` are AWS specific
objects. `locations` are cluster objects.

When specifying multiple regions, you need to manually edit network
configurations:
  - `ec2_vpc` entries must have non-overlapping CIDR networks to allow use of
  AWS VPC peering. By default, TPA sets all CIDR to `10.33.0.0/16`.
  See [VPC](#vpc-required) for more information.
  - Each `location` must be updated with a `subnet` that matches the `ec2_vpc`
  CIDR it belongs to. See [Subnets](#subnets-optional) for more information.
  - TPA creates security groups with basic rules under `cluster_rules`. 
  Those need to be updated to match `ec2_vpc` CIDR for each `subnet` CIDR.
  See [Security groups](#security-groups-optional) for more information.
  - VPC peering must be set up manually before `tpaexec deploy`. We recommend
  creating VPCs and required VPC peering before running `tpaexec configure`
  and using `vpc-id` in `config.yml`. See [VPC](#vpc-required) for more information.

### VPC (required)

You must specify a VPC to use:

    ec2_vpc:
      Name: Test
      cidr: 10.33.0.0/16

This is the default configuration, which creates a VPC named Test, if it doesn't exist, with the
given CIDR. Otherwise, it uses the existing VPC.

To create a VPC, you must specify both the name and the CIDR. If you specify
only a VPC name, TPA fails if a matching VPC doesn't exist.

If TPA creates a VPC,
`tpaexec deprovision` attempts to remove it but leaves any
preexisting VPC alone. (Think carefully before creating new VPCs, because
AWS has a single-digit default limit on the number of VPCs per account.)

If you need more fine-grained matching, or to specify different VPCs in
different regions, you can use the expanded form:

    ec2_vpc:
      eu-west-1:
        Name: Test
        cidr: 172.16.0.0/16
      us-east-1:
        filters:
          vpc-id: vpc-nnn
      us-east-2:
        Name: Example
        filters:
          [filter expressions]

### AMI (required)

You must specify an AMI to use:

    ec2_ami:
      Name: xxx
      Owner: self

You can add filter specifications for more precise matching:

    ec2_ami:
      Name: xxx
      Owner: self
      filters:
        architecture: x86_64
        [more key/value filters]

(By default, `tpaexec configure` selects a suitable `ec2_ami`
for you based on the `--distribution` argument.)

This platform supports Debian 9 (stretch), RedHat Enterprise Linux 7,
Rocky 8, Ubuntu 16.04 (Xenial), and SUSE Linux Enterprise Server 15.

### Subnets (optional)

Every instance must specify its subnet (in CIDR form, or as a subnet-xxx
id). You can optionally specify the name and availability zone for each
subnet that you create:

    ec2_vpc_subnets:
      us-east-1:
        192.0.2.0/27:
          az: us-east-1b
          Name: example1
        192.0.2.100/27:
          az: us-east-1b
          Name: example2

### Security groups (optional)

By default, TPA creates a security group for the cluster. To use one or
more existing security groups, set:

    ec2_groups:
      us-east-1:
        group-name:
          - foo

If you want to customize the rules in the default security group, set
`cluster_rules`:

    cluster_rules:
    - cidr_ip: 0.0.0.0/0
      from_port: 22
      proto: tcp
      to_port: 22
    - cidr_ip: 192.0.2.0/27
      from_port: 0
      proto: tcp
      to_port: 65535
    - cidr_ip: 192.0.2.100/27
      from_port: 0
      proto: tcp
      to_port: 65535

This example permits SSH (port 22) from any address and TCP connections on any
port from specific IP ranges. (`from_port` and `to_port` define a numeric
range of ports, not a source and destination.)

If you set up custom rules or use existing security groups, you must ensure
that instances in the cluster are allowed to communicate with each other as
required (for example, allow tcp/5432 for Postgres).

### Internet gateways (optional)

By default, TPA creates internet gateways for every VPC, unless you set:

    ec2_instance_reachability: private

For more fine-grained control, you can set:

    ec2_vpc_igw:
      eu-west-1: yes
      eu-central-1: yes
      us-east-1: no

### SSH keys (optional)

```
# Set this to change the name under which we register our SSH key.
# ec2_key_name: tpa_cluster_name
#
# Set this to use an already-registered key.
# ec2_instance_key: xxx
```

### S3 bucket (optional)

TPA requires access to an S3 bucket to provision an AWS cluster. This bucket
is used to temporarily store files such as SSH host keys but can also be used for
other cluster data, such as backups.

By default, TPA uses an S3 bucket named `edb-tpa-<aws-account-user-id>`
for any clusters you provision. (If the bucket doesn't exist, you're prompted to
confirm that you want TPA to create it for you.)

To use an existing S3 bucket instead, set:

    cluster_bucket: name-of-bucket

(You can also set `cluster_bucket: auto` to accept the default bucket name without
the confirmation prompt.)

TPA never removes any S3 buckets when you deprovision the cluster. To remove
the bucket yourself, run:

    aws s3 rb s3://<bucket> --force

The IAM user you're using to provision the instances must have read and
write access to this bucket. During provisioning, tpaexec provides
instances with read-only access to the cluster_bucket through the
instance profile.

### Elastic IP addresses

To use elastic IP addresses, set `assign_elastic_ip` to `true` in
`config.yml`. Set it in `instance_defaults` to affect all the instances in your
cluster or set it individually on the separate instances as required. By
default, this setting allocates a new elastic IP address and assigns it to
the new instance.

To use an elastic IP address that has already been allocated but not yet
assigned, use `elastic_ip: 34.252.55.252`, substituting your
allocated address.

### Instance profile (optional)

```
# Set this to change the name of the instance profile role we create.
# cluster_profile: cluster_name_profile
#
# Set this to use an existing instance profile (which must have all the
# required permissions assigned to it).
# instance_profile_name: xxx
```
