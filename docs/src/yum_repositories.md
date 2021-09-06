# Configuring YUM repositories

This page explains how to configure YUM package repositories on RedHat
systems.

You can define named repositories in `yum_repositories`, and decide
which ones to use by listing the names in `yum_repository_list`:

```yaml
cluster_vars:
  yum_repositories:
    Example:
      rpm_url: >-
        https://repo.example.com/repos/Example/example-repo.rpm

  yum_repository_list:
    - EPEL
    - PGDG
    - Example
```

This configuration would install the “repo RPM” for EPEL, PGDG, and the
new Example repository. The repo RPM customarily installs the necessary
`/etc/yum.repos.d/*.repo` files and any GPG keys needed to verify
signed packages from the repository.

The EPEL and PGDG repositories are defined by default. The EPEL
repository is required for correct operation, so you must always
include EPEL in `yum_repository_list`. You should also include PGDG if
you want to install PGDG packages.

You can set `yum_repository_list: []` to not install any repositories
(but things will break without an alternative source of EPEL packages).

To configure a repository which does not have a repo RPM, you can use a
[pre-deploy hook](tpaexec-hooks.md) to install the relevant files
yourself:

```yaml
- name: Define Example repository
  copy:
    dest: /etc/yum.repos.d/example.repo
    owner: root
    group: root
    mode: 0644
    content: |
      [example]
      name=Example repo
      baseurl=https://repo.example.com/repos/Example/
      enabled=1
      gpgkey=https://repo.example.com/repokey.asc
      gpgcheck=1
```

In this case, you do not need to list the repository in
`yum_repository_list`.
