aws
===

TPAexec fully supports provisioning production clusters on AWS EC2.

## API access setup

To use the AWS API, you must:

* [Obtain an access keypair](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
* [Add it to your configuration](https://boto.readthedocs.org/en/latest/boto_config_tut.html)

For example,

```bash
[tpa]$ cat > ~/.aws/credentials
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## Introduction

The service is physically subdivided into
[regions and availability zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html).
An availability zone is represented by a region code followed by a
single letter, e.g., eu-west-1a (but that name may refer to different
locations for different AWS accounts, and there is no way to coordinate
the interpretation between accounts).

AWS regions are completely isolated from each other and share no
resources. Availability zones within a region are physically separated,
and logically mostly isolated, but are connected by low-latency links
and are able to share certain networking resources.

### Networking

All networking configuration in AWS happens in the context of a
[Virtual Private Cloud](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-vpc.html)
within a region. Within a VPC, you can create
[subnets](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Subnets.html)
that is tied to a specific availability zone, along with internet
gateways, routing tables, and so on. 

You can create any number of
[Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html#vpc-security-groups)
to configure rules for what inbound and outbound traffic is permitted to
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
to provide persistent storage to the instance. You can ssh to the
instances by registering an
[SSH public key](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).

Instances are always assigned a private IP address within their subnet.
Depending on the subnet configuration, they may also be assigned an
[ephemeral public IP address](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#concepts-public-addresses)
(which is lost when the instance is shutdown, and a different ephemeral
IP is assigned when it is started again). You can instead assign a
static region-specific routable IP address known as an
[Elastic IP](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)
to any instance.

For an instance to be reachable from the outside world, it must not only
have a routable IP address, but the VPC's networking configuration
(internet gateway, routing tables, security groups) must also align to
permit access.

## Configuration

Here's a brief description of the AWS-specific settings that you can
specify via ``tpaexec configure`` or define directly in config.yml.

### VPC (required)

You must specify a VPC to use.

    ec2_vpc:
      Name: Test

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
          …filter expressions…
      …

### AMI (required)

You must specify an AMI to use.

    ec2_ami:
      Name: xxx
      Owner: self

You can add filter specifications for more precise matching:

    ec2_ami:
      Name: xxx
      Owner: self
      filters:
        architecture: x86_64
        …more «key: value» filters…

(By default, ``tpaexec configure`` will select a suitable ``ec2_ami``
for you based on the ``--distribution`` argument.)

### Subnets (optional)

Every instance must specify its subnet (in CIDR form, or as a subnet-xxx
id). You may optionally specify the name and availability zone for each
subnet that we create:

    ec2_vpc_subnets:
      us-east-1:
        192.0.2.0/27:
          az: us-east-1b
          Name: example1
        192.0.2.100/27:
          az: us-east-1b
          Name: example2
      …

### Security groups (optional)

By default, we create a security group for the cluster. To use one or
more existing security groups, set:

    ec2_groups:
      us-east-1:
        group-name:
          - foo
      …

### Internet gateways (optional)

By default, we create internet gateways for every VPC if

    ec2_instance_reachability: public

is set. For more fine-grained control, you can set

    ec2_vpc_igw:
      eu-west-1: yes
      eu-central-1: yes
      us-east-1: no
      …

### SSH keys (optional)

```
# Set this to change the name under which we register our SSH key.
# ec2_key_name: tpa_cluster_name
#
# Set this to use an already-registered key.
# ec2_instance_key: xxx
```

### S3 bucket (optional)

```
# Set this to upload SSH host keys to a different S3 bucket.
# cluster_bucket: xxx
```

### Instance profile (optional)

```
# Set this to change the name of the instance profile role we create.
# cluster_profile: cluster_name_profile
#
# Set this to use an existing instance profile (which must have all the
# required permissions assigned to it).
# instance_profile_name: xxx
```
