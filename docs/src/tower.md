# TPAexec and Ansible Tower/Ansible Automation Controller

TPAexec can be used with RedHat Ansible Automation Controller (formerly
known as Ansible Tower) by running the configure and provision steps on
a different machine, treating the cluster as a bare-metal one, and then
importing the resulting inventory and other generated files into Tower. A
custom Execution Environment which contains an installation of tpaexec can
then be used for the deployment step and subsequent cluster management.

## Preparing Tower for working with TPAexec

- Add the TPAexec Execution Environment to your Tower installation.

## Setting up a cluster

- Ensure the hosts you intend to use for your cluster are known to your
  Tower installation, that you have a Credential that can access them over
  SSH, and that they have public_ip and private_ip set.

- On a machine with tpaexec installed, prepare a file with a list of
  your hostnames, one per line, with ip addresses:

```text
mercury 34.243.117.57
venus 54.170.86.124
mars 63.35.233.50
jupiter 34.243.13.96
saturn 34.243.196.146
neptune 34.251.84.161
```


- Run `tpaexec configure` giving at least the following arguments:

```bash
[tpa]$ tpaexec configure \
         --use-ansible-tower https://aac.example.com/api \
         --ansible-tower-repository ssh://git@git.example.com/example \
         --hostnames-from <hostnamefile> \
         --platform bare <clustername>
```

  giving the API endpoint of your Tower instance. All
  other options to `tpaexec configure`, as described in [Configuration](tpaexec-configure.md) are still valid.
  This will create a cluster directory named after your cluster.

- config.yml will now include the top-level dictionary `ansible_tower`,
  which will cause `tpaexec provision` to treat the cluster as a Tower
  cluster.

- Edit config.yml if you need to make any other changes.

- Run `tpaexec provision` to generate inventory and other related files.

- Add a Project in Tower with the git repository.

- Add the inventory from the project as an external source to your
  inventory.

- Create a Template in Tower specifying the TPAexec Execution Environment,
  your inventory, and the newly created project. Also include any required
  credentials to reach your hosts, and a credential with a TPA
  subscription token. Set the two variables:

  - tpa_dir: /opt/EDB/TPA
  - cluster_dir: /runner/project/PROJECTNAME

- Run a job based on the new Template to deploy your cluster.
