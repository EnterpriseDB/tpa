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
