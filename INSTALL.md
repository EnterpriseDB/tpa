CustomCloud Installation
========================

To use CustomCloud, you will need Ansible from the
[2ndQuadrant/ansible repository](https://github.com/2ndQuadrant/ansible).

(2ndQuadrant/ansible is a curated version of the official ansible
repository's devel branch, with some additional useful changes that have
not yet been merged upstream.)

The quick version: clone 2ndQuadrant/ansible, export
ANSIBLE_HOME=/path/to/clone, and invoke ansible through the
utils/ansible wrappers provided here.

Python and modules
------------------

You must have Python 2.7.x installed.

Install any packages needed to get pip and virtualenv working. For
example, on Debian, install python-pip and python-virtualenv.

You will need recent versions of the following Python modules:

* jinja2
* boto
* PyCrypto

Install these modules using pip ("pip install jinja2 boto …") rather
than your operating system's packages (which are often too old).

To avoid installing the modules system-wide, they can go into an
ansible-specific virtualenv (recommended):

  virtualenv ~/ansible-python

  # The following line can go into your .bashrc
  source ~/ansible-python/bin/activate

  # With the virtualenv activated, install packages
  pip install jinja2 …

Ansible
-------

Clone the 2ndQuadrant/ansible repository:

    git clone --recursive https://github.com/2ndQuadrant/ansible

Set ANSIBLE_HOME in your environment (and .bashrc):

    export ANSIBLE_HOME=/path/to/ansibledir

Now you should be able to run ./utils/ansible and the other scripts in
this repository. The following simple tests should succeed if Ansible
has been installed correctly:

    ./utils/ansible localhost -m ping
    ./utils/ansible localhost -c ssh -a "id"

[The Ansible installation docs](http://docs.ansible.com/ansible/intro_installation.html)
have more details about running from a source checkout.

If you have trouble getting Ansible working, write to Abhijit, Richard,
or Ian for help.

Other software
--------------

The [AWS CLI](https://aws.amazon.com/cli/) can be useful, but you
probably won't need it. If you do, follow the instructions at
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ec2-cli-get-set-up.html
