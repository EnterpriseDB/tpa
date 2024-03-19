# TPA and Ansible Tower/Ansible Automation Platform

TPA has support for RedHat Ansible Automation Platform (AAP) an automation controller.
You run only deploy and upgrade steps on AAP. You run configuration and provisioning on a
standalone machine with the tpa package installed. You can then import the resulting cluster
directory on AAP. Support is limited to bare-metal
platforms.

## AAP initial setup

Before TPA can use AAP to deploy clusters, you need to perform this initial setup.

### Add TPA Execution Environment image (admin)

Starting with version 2.4, AAP uses container images to run Ansible playbooks.
These containers, called Execution Environments (EE), bundle dependencies
required by playbooks to run successfully.

!!! Note
    EDB customers can reach out to EDB Support for help with EE.

As an AAP admin, create an entry in your available EE list that points to
your EE image.

### Create the EDB_SUBSCRIPTION_TOKEN credential type (admin)

As an AAP admin, create the custom credential type
`EDB_SUBSCRIPTION_TOKEN`to hold your EDB
subscription access token:

1. Go to the Credentials Type page in the AAP UI.

1. Set the **Name** field to `EDB_SUBSCRIPTION_TOKEN`.

1. Paste the following into the **Input Configuration** field:

    ```yaml
    fields:
    - id: tpa_edb_sub_token
      type: string
      label: EDB_SUBSCRIPTION_TOKEN
      secret: true
    required:
    - tpa_edb_sub_token
    ```
1. Paste the following into the **Injector Configuration** field:

    ```yaml
    env:
      EDB_SUBSCRIPTION_TOKEN: '{{ tpa_edb_sub_token }}'
    ```

1. Save the changes.

1. Create a credential using the newly added type `EDB_SUBSCRIPTION_TOKEN`.

## Setting up a cluster

Perform the initial steps on a workstation with the tpaexec package installed.

### On the TPA workstation

#### Configure

Run the `tpaexec configure` command, including these options:
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

`--use-ansible-tower` expects the AAP address as a parameter even if it
isn't used at the time. `--tower-git-repository` is used to import the
cluster data into AAP. TPA creates its own branch using `cluster_name`
as the branch name, which allows you to use the same repository for all
of your clusters. All other options to `tpaexec configure`, as
described in [Configuration](tpaexec-configure.md), are still valid.

#### config.yml modification

`config.yml` includes the top-level dictionary `ansible_tower`, which
causes `tpaexec provision` to treat the cluster as an AAP-enabled
cluster.

Edit `config.yml` to ensure that `ansible_host` and `{private,public}_ip`
are defined for each node and `ansible_host` is set to a value that AAP can
resolve. Make any change or addition needed. See [Cluster
configuration](configure-cluster.md).

To generate inventory and other related files, run `tpaexec provision` .

### On the AAP UI

#### Project

Add a project in AAP using the git repository as the source.
Set the default EE to use the image provided by TPA.

!!! Note Project options

    To ensure changes are correctly synced before running a job,
    we strongly recommend using **Update Revision on Launch**.

    **Allow Branch Override** is required when trying to use multiple
    inventories with a single project.

#### Inventory

Add an empty inventory. Use the project as an external source to
populate it using `inventory/00-cluster_name` as the inventory file.

!!! Note Inventory options

    To ensure changes are correctly synced, We strongly recommend using
    **Overwrite local groups and hosts from remote inventory source**.

    We also recommend using **Overwrite local variables from remote inventory source** when not setting
    additional variables outside TPA's control in AAP.

#### Credentials

Create a `vault` credential. You can retrieve the vault password using
`tpaexec show-vault <cluster_dir>` on the TPA workstation.

To connect to your inventory nodes by way of SSH during deployment,
make sure the machine credential is available in AAP.

#### Template creation

To create a template:

1. Create a template that uses your project and your inventory.

1. Include these required credentials:
    - Vault credential
    - `EDB_SUBSCRIPTION_TOKEN` credential
    - Machine credential

1. Set two additional variables:

    ```yaml
    tpa_dir: /opt/EDB/TPA
    cluster_dir: /runner/project
    ```

1. Select `deploy.yml` as the playbook.

1. To deploy your cluster, run a job based on the new template.

## Use one project for multiple inventory

TPA uses a different branch name for each of your clusters in the
associated git repository. This approach allows the use of a single project for
multiple clusters.

### Set Allow branch override option

In the AAP project, enable the **Allow branch override** option.

### Define multiple inventories

TPA uses a different branch name for each of your clusters in the git
repository. You can generate multiple inventories using the same project
as the source by overriding the branch for each inventory.

### Define credentials per inventory

Ensure vault passwords are set accordingly per inventory since these
differ on each TPA cluster.

## Update TPA on AAP

Updating TPA on AAP involves some extra steps.

### Update TPA workstation package

Update your TPA workstation package as any OS package
depending on your OS. See [Installation](INSTALL.md).

### Use EE image with same version tag

Modify the EE image in AAP to use the same version tag as the
workstation package version used.

### Run tpaexec relink on your cluster directory

Ensure that any cluster using AAP is up to date by running `tpaexec
relink <cluster_dir>`. Be sure to push any change committed by
the `relink` command:

```bash
$ git status
On branch cluster_name
Your branch is ahead of 'tower/cluster_name' by 1 commit.
  (use "git push" to publish your local commits)
...
$ git push tower
```

### Sync project and inventories

If they aren't set to use **Update revision on job launch** and **Update on launch**,
sync the project in the AAP UI and related inventories,
respectively.
