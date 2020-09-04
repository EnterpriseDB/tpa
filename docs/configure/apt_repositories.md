# Configuring APT repositories

This page explains how to configure APT package repositories on Debian
and Ubuntu systems.

You can define named repositories in `apt_repositories`, and decide
which ones to use by listing the names in `apt_repository_list`:

```yaml
cluster_vars:
  apt_repositories:
    Example:
      key_id: XXXXXXXX
      key_url: https://repo.example.com/path/to/XXXXXXXX.asc
      repo: >-
        deb https://repo.example.com/repos/Example/ xxx-Example main

  apt_repository_list:
    - PGDG
    - Example
```

This configuration would install the GPG key (with id `key_id`,
obtained from `key_url`) and a new entry under
`/etc/apt/sources.list.d` with the given `repo` line (or lines)
for the PGDG repository (which is already defined by default) and the
new Example repository.

When you configure additional repositories, remember to include PGDG in
`apt_repository_list` if you still want to install PGDG packages.

You can set `apt_repository_list: []` to not install any repositories.
