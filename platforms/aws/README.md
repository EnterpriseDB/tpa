TPA on AWS
==========

Access setup
------------

To use the AWS API, you need an access key id and a secret access key.

Use **Create Access Key** in the **Security Credentials** tab for your
AWS IAM user to generate an access key, as described by
http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html

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

Write to Abhijit if you need help.
