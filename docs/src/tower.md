# TPA and Ansible Tower/Ansible Automation Controller

TPA has support for RedHat Ansible Automation Controller (AAP). Only
deploy/upgrade steps are run on AAP. Configure and provision run on a
standalone machine with tpa package installed, resulting cluster
directory can then be imported on AAP. Support is limited to bare metal
platform.

## Automation Platform initial setup

TPA needs the following steps to be done once before being able to use
AAP to deploy clusters.

### Add TPA Execution Environment image (admin)

Starting version 2.4 AAP uses container images to run ansible playbooks.
These containers, called Execution Environment (EE), bundle dependencies
required by playbooks to run successfully.

!!! Note:
  EDB customers can reach out to EDB support for help with the Execution
  Environment (EE)

As an AAP admin, create an entry in your available EE list pointing to
your EE image.


### Create the EDB_SUBSCRIPTION_TOKEN credential type (admin)

As an AAP admin, create the custom credential type
`EDB_SUBSCRIPTION_TOKEN` as described below to hold your EDB
subscription access token:

Go to the Credentials Type page in AAP UI.

Set the "NAME" field to "EDB_SUBSCRIPTION_TOKEN".
Paste the following to "INPUT CONFIGURATION" field:

```yaml
fields:
- id: tpa_edb_sub_token
  type: string
  label: EDB_SUBSCRIPTION_TOKEN
  secret: true
required:
- tpa_edb_sub_token
```

Paste the following to "INJECTOR CONFIGURATION" field:

  ```yaml
  env:
    EDB_SUBSCRIPTION_TOKEN: '{{ tpa_edb_sub_token }}'
  ```
Save the changes.

Create a credential using the newly added type `EDB_SUBSCRIPTION_TOKEN`.

## Setting up a cluster

Initial steps are run on a workstation with tpaexec package installed.

### On the TPA workstation:

#### Configure

Run `tpaexec configure` command including these options:
  `--platform bare`, `--use-ansible-tower`, `--tower-git-repository`

```bash
[tpa]$ tpaexec configure <clustername> \
         --platform bare \
         --use-ansible-tower https://aac.example.com \
         --tower-git-repository ssh://git@git.example.com/example \
         --hostnames-from <hostnamefile> \
         --architecture PGD-Always-ON \
         --pgd-proxy-routing local \
         --postgresql 16
```

`--use-ansible-tower` expects the AAP address as parameter even if it
isn't used at the time. `--tower-git-repository` is used to import the
cluster data into AAP; TPA creates its own branch using `cluster_name`
as the branch name (This allows you to use the same repository for all
of your clusters). All other options to `tpaexec configure`, as
described in [Configuration](tpaexec-configure.md), are still valid.

#### config.yml modification

config.yml includes the top-level dictionary `ansible_tower`, which
causes `tpaexec provision` to treat the cluster as an AAP enabled
cluster.

Edit config.yml, ensure that `ansible_host` and `{private,public}_ip`
are defined for each node and ansible_host is set to a value that can be
resolved by AAP. Make any change or addition needed, see [Cluster
Configuration](configure-cluster.md).

Run `tpaexec provision` to generate inventory and other related files.

### On AAP UI:

#### Project

Add a Project in AAP using the git repository as source.
Set default EE to use tpa provided image.

!!! Note on project options

  Use of `Update Revision on Launch` is strongly suggested to ensure
  changes are correctly synced before running a job.

  `Allow Branch Override` is required when trying to use multiple
  inventory with a single project.

#### Inventory

Add an empty inventory, use the project as an external source to
populate it using `inventory/00-cluster_name` as inventory file.

!!! Note on inventory options

  Use of `Overwrite local groups and hosts from remote inventory source`
  is strongly suggested to ensure changes are correctly synced.

  `Overwrite local variables from remote inventory source` is also
  suggested when not setting additionnal variables outside TPA's control
  in AAP.

#### Credentials

Create a `vault` credential. The vault password can be retrieved via
`tpaexec show-vault <cluster_dir>` on the tpa workstation.

Ensure the machine credential is available in AAP to connect to your
inventory nodes via ssh during deployment.

#### Template creation

Create a Template that uses your project and your inventory.
Include required credentials:
- vault credential
- EDB_SUBSCRIPTION_TOKEN credential
- machine credential

Set two additional variable:
```
  tpa_dir: /opt/EDB/TPA
  cluster_dir: /runner/project
```
Select `deploy.yml` as playbook.

Run a job based on the new Template to deploy your cluster.

## Use one project for multiple inventory

TPA uses a different branch name for each of your cluster in the
associated git repository. This allows the use of a single project for
multiple clusters.

### Set Allow branch override option

Enable the `Allow branch override option` in the AAP project.

### Define multiple inventory

TPA uses a different branch name for each of your cluster in the git
repository. Multiple inventory can be generated using the same project
as source but overriding the branch for each inventory.

### Define credentials per inventory

Ensure vault password are set accordingly per inventory since these will
differ on each TPA cluster.

## Update TPA on AAP

Updating TPA on AAP involves some extra steps.

### Update tpa workstation package

Update your TPA workstation package as any OS package
depending on your OS. See [Installation](INSTALL.md).

### Use EE image with same version tag

Modify the EE image in AAP to use the same version tag as the
workstation package version used.

### Run tpaexec relink on your cluster directory

Ensure that any cluster using AAP is up to date by running `tpaexec
relink <cluster_dir>`. Ensure that you push any change committed by
`relink` command.
```
$ git status
On branch cluster_name
Your branch is ahead of 'tower/cluster_name' by 1 commit.
  (use "git push" to publish your local commits)
...
$ git push tower
```

### Sync project and inventories

Sync the project in AAP UI and related inventories if these are not set
to use `Update revision on job launch` and `Update on launch`
respectively.
