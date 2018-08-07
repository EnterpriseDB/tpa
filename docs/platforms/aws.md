AWS
===

## Access setup

To use the AWS API, you need an access key id and a secret access key.

Use **Create Access Key** in the **Security Credentials** tab for your
AWS IAM user to generate an access key, as described by
https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html

Next, make the keypair available to the boto library, as described by
https://boto.readthedocs.org/en/latest/boto_config_tut.html

There are two easy ways to do this:

1. Set environment variables:

   ```
   export AWS_ACCESS_KEY_ID='AKIAIOSFODNN7EXAMPLE'
   export AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
   ```

2. Create ~/.aws/credentials with the following contents:

   ```
   [default]
   aws_access_key_id = AKIAIOSFODNN7EXAMPLE
   aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

### AWS Fundamentals

The AWS Elastic Compute Cloud (**EC2**) is physically subdivided first into [Regions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html) and further into Availability Zones. Each Availability Zone is isolated, but the Availability Zones in a region are connected through low-latency links. An Availability Zone is represented by a region code followed by a letter identifier; e.g. `eu-east-1a`. Note that `eu-east-1a` might not be the same location as `eu-east-1a` for another account, and there is no way to coordinate Availability Zones between accounts.

Within Availability Zones, you can create [**Instances**](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Instances.html) (Virtual Machines) and storage volumes.

The instances are built using templates known as [Amazon Machine Images (**AMI**s](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html)), which can be preconfigured with OS and bespoke packages, allowing for fast deployment times. These AMIs are region specific, so when creating them, make sure that they are available in each region that you will be using.

Amazon have various HW configs available, known as **[Instance Types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html)**, with various price performance points. 

The storage volumes that we use are called [Amazon Elastic Block Store (**EBS**)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AmazonEBS.html) volumes, which provide persistent storage for the server instances.

To specify the protocols, ports, and source IP ranges that can reach the server instances, you can define **[Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html#vpc-security-groups)**, which are effectively a set of firewall rules.

You can create Virtual networks which are logically isolated from the rest of the AWS cloud, and can optionally be connected to your own network - these are known as virtual private clouds ([**VPC**s](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-vpc.html))

It is possible to assign Static IPv4 addresses to instances, known as **[Elastic IP](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)** addresses, or to allow AWS to assign a public IP address from the EC2-VPC public IPv4 address pool. Elastic IPs are region specific, externally accessible IPv4 addresses that are associated with your AWS account, and can be quickly associated with any instance in that region. When you allow AWS to configure an [external IPv4 address](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html#concepts-public-addresses), it is configured at instance boot time. *Note this address is released at shutdown time, and it is not possible to retain the same address after reboot.*

During instance build, [key pairs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) are created/assigned to allow secure login to the instances. (It is possible to assign existing keys to the instances). If you lose your private key, you will irrevocably lose access to the instances - having access to the AWS console does not help.

## Configuration

This is a list of the AWS-specific configuration settings that you can
define in config.yml

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
