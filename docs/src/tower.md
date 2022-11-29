# TPAexec and Ansible Tower/Ansible Automation Controller

TPAexec can be used with RedHat Ansible Automation Controller (formerly
known as Ansible Tower) by running the configure and provision steps on
a standalone machine, treating the cluster as a bare-metal one, and then
importing the resulting inventory and other generated files into Tower.

A TPAexec installation on Tower instance, which includes its own virtual
environment (tpa-venv), is then used for the deployment step in Tower.

This document describes the appropriate procedure for Ansible Tower
version 3.8.

## Preparing Tower for working with TPAexec

### Setting up a TPAexec virtual environment

- Install tpaexec on your Tower server under /opt/EDB/TPA. This is the
  default location when TPAexec is installed from package.
- Run `tpaexec setup` which will create a virtual environment under
  /opt/EDB/TPA/tpa-venv and install the required packages.
- Add TPAexec directory (/opt/EDB/TPA) to the "CUSTOM VIRTUAL ENVIRONMENT PATHS"
  field in the System Settings page of Tower UI.
- Ansible Tower 3.8 has psutil as dependency, which is not available in
  the default Tower virtual environment. To install psutil, run the
  following command in the Tower virtual environment:
  `sudo pip install psutil`

### Creating the TPA_2Q_SUBSCRIPTION_TOKEN credential type

Create the custom credential type called "TPA_2Q_SUBSCRIPTION_TOKEN"
as described below:

- Go to the Credentials Type page in Tower UI.
- Set the "NAME" field to "TPA_2Q_SUBSCRIPTION_TOKEN".
- Paste this to "INPUT CONFIGURATION" field:

  ```yaml
  fields:
  - id: tpa_2q_sub_token
    type: string
    label: TPA_2Q_SUBSCRIPTION_TOKEN
  required:
  - tpa_2q_subscription_token
  ```

- Paste this to "INJECTOR CONFIGURATION" field:

  ```yaml
  env:
    TPA_2Q_SUBSCRIPTION_TOKEN: '{{ tpa_2q_sub_token }}'
  ```
- Click "SAVE" button.

## Setting up a cluster

- Ensure the hosts you intend to use for your cluster are known to your
  Tower installation, that you have a Credential that can access them over
  SSH, and that they have ansible_host, public_ip and private_ip set.

- On a machine with tpaexec installed, prepare a file with a list of
  your hostnames, one per line:

```text
mercury
venus
mars
jupiter
saturn
neptune
```


- Run `tpaexec configure`:

```bash
[tpa]$ tpaexec configure <clustername> \
         --platform bare \
         --use-ansible-tower https://aac.example.com/api \
         --tower-git-repository ssh://git@git.example.com/example \
         --hostnames-from <hostnamefile> \
         --architecture BDR-Always-ON \
         --layout bronze \
         --harp-consensus-protocol bdr
```

  The API endpoint is currently accepted and added to config.yml but
  not used.  The git repository will be used to import the cluster data
  into Tower; tpaexec will create its own branch in the repository
  for this cluster so it doesn't matter what branches already exist
  in it. (This allows you to use the same repository for all of your
  clusters.)  All other options to `tpaexec configure`, as described in
  [Configuration](tpaexec-configure.md) are still valid.

  This will create a cluster directory named after your cluster.

- config.yml will now include the top-level dictionary `ansible_tower`,
  which will cause `tpaexec provision` to treat the cluster as a Tower
  cluster.

- Edit config.yml if you need to make any other changes.

- Run `tpaexec provision` to generate inventory and other related files.

- Add a Project in Tower with the git repository.

- Add the inventory from the project as an external source to your
  inventory.

- Create a Template in Tower specifying the TPAexec virtual environment,
  your inventory, and the newly created project. Also include any required
  credentials to reach your hosts, and a credential with a TPA
  subscription token (TPA_2Q_SUBSCRIPTION_TOKEN).

- Set one additional variable: `tpa_dir: /opt/EDB/TPA`

- Run a job based on the new Template to deploy your cluster.
