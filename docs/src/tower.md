---
description: Deploying and managing TPA clusters using Ansible Tower/Ansible Automation Platform.
---

# TPA and Ansible Tower/Ansible Automation Platform

TPA supports deployments via RedHat Ansible Automation Platform (AAP).
The support, as detailed below, works by allowing you to run `deploy`
and `upgrade` steps on AAP. Before you can run deploy or upgrades
(later), you will need to run configuration (`configure` command) and
provisioning (`provision` command) on a separate standalone machine that
has tpa packages installed. Once you have run `configure` and
`provision` on this standalone machine with suitable options, you can
then import the resulting cluster directory on AAP. Support is limited
to bare-metal platforms.

## AAP initial setup

Before TPA can use AAP to deploy clusters, you need to perform this
initial setup.

### Add TPA Execution Environment image (admin)

Starting with version 2.4, AAP uses container images to run Ansible
playbooks. These containers, called Execution Environments (EE), bundle
dependencies required by playbooks to run successfully. As a
consequence, this means that in order to, resolve and use all required
TPA dependencies, you will need an EE that includes TPA so your AAP can
use it when running deployments and upgrades.

!!! Note Get an EE

    See [Build an EE for TPA](#build-an-ee-for-tpa) for instructions on
    building your own image.

    EDB customers can reach out to EDB Support for help with EE.

As an AAP admin, create an entry in your available EE list that points
to your TPA enabled EE image.

### Create the EDB_SUBSCRIPTION_TOKEN credential type (admin)

As an AAP admin, create the custom credential type
`EDB_SUBSCRIPTION_TOKEN`to hold your EDB subscription access token:

1. Go to the Credentials Type page in the AAP UI.

2. Set the **Name** field to `EDB_SUBSCRIPTION_TOKEN`.

3. Paste the following into the **Input Configuration** field:

    ```yaml
    fields:
    - id: tpa_edb_sub_token
      type: string
      label: EDB_SUBSCRIPTION_TOKEN
      secret: true
    required:
    - tpa_edb_sub_token
    ```
4. Paste the following into the **Injector Configuration** field:

    ```yaml
    env:
      EDB_SUBSCRIPTION_TOKEN: '{{ tpa_edb_sub_token }}'
    ```

5. Save the changes.

6. Create a credential using the newly added type
   `EDB_SUBSCRIPTION_TOKEN`.

## Setting up a cluster

Perform the initial steps on a workstation with the tpaexec packages
installed.

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
of your clusters. All other options to `tpaexec configure`, as described
in [Configuration](tpaexec-configure.md), are still valid.

#### config.yml modification

`config.yml` includes the top-level dictionary `ansible_tower`, which
causes `tpaexec provision` to treat the cluster as an AAP-enabled
cluster.

Edit `config.yml` to ensure that `ansible_host` and
`{private,public}_ip` are defined for each node and `ansible_host` is
set to a value that AAP can resolve. Make any further changes or
additions that you may need. See [Cluster
configuration](configure-cluster.md) for more details.

To generate inventory and other related files, run `tpaexec provision`.

### On the AAP UI

#### Project

Add a project in AAP using the git repository as the source. Set the
default EE of the project to use the TPA EE image.

!!! Note Project options

    To ensure changes are correctly synced before running a job, we
    strongly recommend using **Update Revision on Launch**.

    **Allow Branch Override** is required when trying to use multiple
    inventories with a single project.

#### Inventory

Add an empty inventory. Use the project as an external source to
populate it using `inventory/00-cluster_name` as the inventory file.

!!! Note Inventory options

    To ensure changes are correctly synced, we strongly recommend using
    **Overwrite local groups and hosts from remote inventory source**.

    We also recommend using **Overwrite local variables from remote
    inventory source** when not setting additional variables outside
    TPA's control in AAP.

#### Credentials

Create a `vault` credential. You can retrieve the vault password using
`tpaexec show-vault <cluster_dir>` on the TPA workstation.

To connect to your inventory nodes by way of SSH during deployment, make
sure the machine credential is available in AAP.

#### Template creation

To create a template:

1. Create a template that uses your project and your inventory.

2. Include these required credentials:
    - Vault credential
    - `EDB_SUBSCRIPTION_TOKEN` credential
    - Machine credential

3. Set two additional variables:

    ```yaml
    tpa_dir: /opt/EDB/TPA
    cluster_dir: /runner/project
    ```

4. Select `deploy.yml` as the playbook.

5. To deploy your cluster, run a job based on the new template.

## Use one project for multiple inventory

TPA uses a different branch name for each of your clusters in the
associated git repository. This approach allows the use of a single
project for multiple clusters.

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

Update your TPA workstation package as any OS package depending on your
OS. See [Installation](INSTALL.md).

### Use EE image with same version tag

Modify the EE image in AAP to use the same version tag as the
workstation package version used.

### Run tpaexec relink on your cluster directory

Ensure that any cluster using AAP is up to date by running `tpaexec
relink <cluster_dir> --force`. An example of when you need to do this is
after you have upgraded your TPA installation to a new version. Be sure
to push any change committed by the `relink` command:

```bash
$ git status
On branch cluster_name
Your branch is ahead of 'tower/cluster_name' by 1 commit.
  (use "git push" to publish your local commits)
...
$ git push tower
```

### Sync project and inventories

If they aren't set to use **Update revision on job launch** and
**Update on launch**, sync the project in the AAP UI and related
inventories, respectively.

## Build an EE for TPA

### Prerequisites

In order to build your own EE image, we recommend using
`ansible-builder`.

You need:
1. `docker` or `podman`
2. `ansible-builder` and `ansible-navigator` python toolkits
3. TPA source code checked out at tag `vA.B.C` from [TPA
   repo](https://github.com/EnterpriseDB/tpa) where `vA.B.C` is the TPA
   version you want to use.

### Environment file

`ansible-builder` uses an environment file to help generate a working EE
image.

Here is a template example of such an environment file for TPA:

**execution-environment.yml**
```yaml
version: 3
images:
  base_image:
    name: 'registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest'
dependencies:
  python: << TPA_REPO_CLONE_FOLDER >>/requirements-aap.txt
  galaxy: << TPA_REPO_CLONE_FOLDER >>/collections/requirements.yml
options:
  package_manager_path: /usr/bin/microdnf

additional_build_steps:
  append_final:
   - RUN mkdir -p /opt/EDB/TPA
   - COPY << TPA_REPO_CLONE_FOLDER >> /opt/EDB/TPA
   - ENV PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}/opt/EDB/TPA/lib"
```

!!! Note Base image

    Base image used here requires access to registry.redhat.io (should
    be provided alongside AAP license). This image already comes with
    most of the requirements for AAP 2.4 such as `python 3.12.*`,
    `ansible-core==2.16.*`, and `ansible-runner` which simplify the
    task.

    Different base image may require more `additional_build_steps`. See
    [ansible-builder](https://ansible.readthedocs.io/projects/builder/en/latest/)
    for advanced usage.

### EE build command

The following command should build the EE image for you:

```bash
ansible-builder build \
  --file=execution-environment.yml \
  --container-runtime=<docker/podman> \
  --tag=<your-registry>/<your-namespace>/tpa-ee:vA.B.C \
  --verbosity 2
  ```
