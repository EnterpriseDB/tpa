CustomCloud cluster configuration
=================================

To bring up a cluster with CustomCloud, you will need to write two YAML
files: **config.yml** describes the instances required; **deploy.yml**
is a playbook that maps the desired roles to the provisioned instances.

These files should be in a cluster-specific directory; the location must
be passed to playbooks using «-e cluster=path/to/dir» on the command
line to set the variable named "cluster".

There are several examples in this directory. Start with test/

For help with YAML syntax, see
http://docs.ansible.com/ansible/YAMLSyntax.html

Provisioning
------------

Provisioning starts with a description of a cluster and ends with the
desired instances running and accessible by ssh. config.yml defines
variables used by the provisioning process.

The following variables must be defined:

1. **cluster_name** (a string)
2. **cluster_tags** (a hash of tag names and values)
3. **instances** (an array of hashes, one per instance).

The contents of config.yml are platform-specific; the above applies to
AWS, which is the only platform we currently support.

Hybrid clusters
---------------

Provisioning is independent of configuration and deployment, so clusters
may comprise physical servers, EC2 instances, or instances provisioned
on different platforms; if they are accessible via ssh, they can be in
the cluster.

The $cluster_dir/inventory/ directory contains static inventory files
and dynamic inventory scripts that tell ansible how to connect to the
provisioned hosts.

The AWS provisioning process writes a static inventory file with the IP
addresses and main group definition for the provisioned instances. This
can be augmented by facts from the inventory/ec2.py script if needed.

For more about Ansible inventory files, see
http://docs.ansible.com/ansible/intro_inventory.html and
http://docs.ansible.com/ansible/intro_dynamic_inventory.html

Deployment
----------

deploy.yml is an Ansible playbook. It consists of one or more plays that
target the provisioned hosts and applies the desired roles to them, as
well as performing any other deployment tasks needed.

Hosts must be targeted not by name but by their attributes, e.g., group
memberships or tag values (which are translated to group memberships by
the ec2 inventory plugin). For example,

    - hosts: tag_Name_SomeCluster
      roles:
        - …

would target all hosts in the cluster, while

    - hosts: tag_Name_SomeCluster:&tag_db_primary

would target any hosts in the cluster with a tag named "db" with the
value "primary".

It's also possible (but less desirable, at least for reasons of clarity)
to apply roles conditionally. For example,

    - hosts: all
      roles:
        - { role: 'somerole', when: "…some condition…" }
        - otherrole

would apply somerole only to the hosts for which the condition evaluates
to true, and otherrole to all hosts.

For more about Ansible playbooks, see
http://docs.ansible.com/ansible/playbooks.html
and
http://docs.ansible.com/ansible/intro_patterns.html
for host patterns.

Ask for help if you need it
---------------------------

If you can't figure out how to express your cluster in terms of the
configuration files described above, or you are having some other
problem, write to Abhijit or Haroon for help.
