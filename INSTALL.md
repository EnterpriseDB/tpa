Custom Cloud Installation
=========================

Requirements
------------

Python 2.7.x

Recent versions of PyCrypto, jinja2, and boto. Install using pip rather
than packages. (Other Python libraries may also be needed.)

Ansible 2.x
    https://github.com/2ndQuadrant/ansible
    http://docs.ansible.com/ansible/intro_installation.html

Use 2ndQuadrant/ansible in preference to ansible/ansible; the former is
tested and includes local changes not present upstream. Install Ansible
by cloning the git repository, export ANSIBLE_HOME=/path/to/clone, and
invoke ansible* through the utils/ansible* wrappers provided here.

The AWS CLI is useful and recommended, though not exactly required.
    https://aws.amazon.com/cli/

Installation
------------

Install Python 2.7 from operating system packages. For example, you need
the python, python-pip, and python-virtualenv packages on Debian.

Next, create a Python virtualenv in any convenient directory:

    virtualenv ~/ansible-python

    # The following line can go into your .bashrc
    source ~/ansible-python/bin/activate

Install the required Python packages:

    pip install PyYAML jinja2 PyCrypto boto

Install Ansible:

    git clone --recursive https://github.com/2ndQuadrant/ansible

And set ANSIBLE_HOME in your environment (and .bashrc):

    export ANSIBLE_HOME=/path/to/ansibledir

Now you should be able to run ./utils/ansible and the other scripts in
this repository. The following simple tests should succeed if Ansible
has been installed correctly:

    ./utils/ansible localhost -m ping
    ./utils/ansible localhost -c ssh -a "id"

For convenience, you can also install the AWS cli according to the
following instructions:
    http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ec2-cli-get-set-up.html
