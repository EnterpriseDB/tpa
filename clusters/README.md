CustomCloud cluster configuration
=================================

To bring up a cluster with CustomCloud, you will need to write two YAML
files: **config.yml** describes the instances required; **deploy.yml**
maps the desired roles to the provisioned instances.

There are several examples in this directory. Start with test/

For help with YAML syntax, see
http://docs.ansible.com/ansible/YAMLSyntax.html

Provisioning
------------

config.yml defines variables used by the provisioning process. It must
define **cluster_name** (a string), **cluster_tags** (a hash of tag
names and values), and **instances** (an array of hashes, one per
instance).

Deployment
----------

deploy.yml is an Ansible playbook. It consists of one or more plays that
target the provisioned hosts and applies the desired roles to them, as
well as performing any other deployment tasks needed.

For more about Ansible playbooks, see
http://docs.ansible.com/ansible/playbooks.html

Hybrid clusters
---------------

If your cluster is to contain hosts that aren't AWS EC2 instances, you
need to add inventory files to define them.

For more about Ansible inventory files, see
http://docs.ansible.com/ansible/intro_inventory.html and
http://docs.ansible.com/ansible/intro_dynamic_inventory.html

Ask for help if you need it
---------------------------

If you can't figure out how to express your cluster in terms of the
configuration files described above, or you are having some other
problem, write to Abhijit or Haroon for help.
