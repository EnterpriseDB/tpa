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

    Other:
      description: "Optional repository description"
      baseurl: https://other.example.com/repos/Other/$basearch
      gpgkey:
        https://other.example.com/repos/Other/gpg.XXXXXXXXXXXXXXXX.key

  yum_repository_list:
    - EPEL
    - PGDG
    - Example
    - Other
```

This example shows two ways to define a YUM repository.

If the repository has a “repo RPM” (a package that customarily installs
the necessary `/etc/yum.repos.d/*.repo` file and any GPG keys needed to
verify signed packages from the repository), you can just point to it.

Otherwise, you can specify a description, a `baseurl`, and a `gpgkey`
URL, and TPA will create a `/etc/yum.repos.d/Other.repo` file for
you based on this information.

The EPEL and PGDG repositories are defined by default. The EPEL
repository is required for correct operation, so you must always
include EPEL in `yum_repository_list`. You should also include PGDG if
you want to install PGDG packages.

You can set `yum_repository_list: []` to not install any repositories
(but things will break without an alternative source of EPEL packages).

If you need to perform any special steps to configure repository access,
you can use a [pre-deploy hook](tpaexec-hooks.md) to create the .repo
file yourself:

```yaml
- name: Define Example repository
  copy:
    dest: /etc/yum.repos.d/example.repo
    owner: root
    group: root
    mode: "0644"
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
