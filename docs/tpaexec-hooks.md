# TPAexec hooks

TPAexec can set up fully-functional clusters with custom configuration
by itself, but it allows you to write hook scripts to execute arbitrary
Ansible tasks during the deployment.

TPAexec already provides a broad variety of settings to control your
cluster configuration, including custom repositories, custom packages,
custom Postgres configuration (both pg_hba.conf and postgresql.conf),
and so on. You can use hooks to address specific needs that are not met
by the various configuration settings.

If you create files with specific names under the ``hooks`` subdirectory
of your cluster directory, TPAexec will invoke them at various stages of
the deployment process.

```
$ mkdir cluster_dir/hooks
$ cat > cluster_dir/hooks/pre-deploy.yml
---
- debug: msg="hello world!"
```

This is the ultimate extension mechanism for TPAexec. There is no limit
to what you can do with hooks. Please use them with caution.

Please keep in mind the additional maintenance burden of custom hooks.
The TPAexec developers have no insight into your hook code, and cannot
guarantee compatibility between releases beyond invoking hooks at the
expected stage.

Hook scripts are invoked with ``include_tasks``, so they are expected to
be YAML files containing a list of Ansible tasks (not a playbook, which
contains a list of plays). Unless otherwise documented below, hooks are
unconditionally executed for all hosts in the deployment.

## Currently supported hooks

### pre-deploy

The pre-deploy hook (``hooks/pre-deploy.yml``) is invoked early during
the deployment, after Python has been bootstrapped, but before package
installation or any other actions.

This hook may be used to set up custom repository configuration, beyond
what the ``apt_repositories`` or ``yum_repositories`` settings can do.

### post-repo

The post-repo hook (``hooks/post-repo.yml``) is invoked after package
repositories have been configured.

This hook may be used to make corrections to the normal repository
configuration before commencing package installation.

### pre-initdb

The pre-initdb hook (``hooks/pre-initdb.yml``) is invoked before testing
if PGDATA exists and running initdb to create it.

You should not ordinarily need to use this hook.

### postgres-config

The postgres-config hook (``hooks/postgres-config.yml``) is invoked
after TPAexec has generated Postgres configuration files, including
pg_hba.conf and the files in conf.d, but before the server has been
started.

This hook can be used, for example, to create a pg_ident.conf file.

### postgres-config-final

The postgres-config-final hook (``hooks/postgres-config-final.yml``) is
invoked after Postgres has been started and the required extensions have
been created.

This hook can be used to perform custom extension configuration.

### postgres-pre-update

The postgres-pre-update hook (``hooks/postgres-pre-update.yml``) is
invoked by the ``tpaexec update-postgres`` command before it installs
any new Postgres packages.

### postgres-post-update

The postgres-post-update hook (``hooks/postgres-post-update.yml``) is
invoked by the ``tpaexec update-postgres`` command after the package
installation has been completed.

### bdr-pre-node-creation

The bdr-pre-node-creation hook (``hooks/bdr-pre-node-creation.yml``) is
invoked before creating a BDRv3 node for the first time. It will not be
invoked if the node already exists.

### bdr-post-group-creation

The bdr-post-group-creation hook (``hooks/bdr-post-group-creation.yml``)
is invoked after creating a BDRv3 node group on the
``first_bdr_primary`` instance.

### post-deploy

The post-deploy hook (``hooks/post-deploy.yml``) is invoked at the end
of the deployment process.

## New hooks

2ndQuadrant adds new hooks to TPAexec as the need arises. If your use
case is not covered by the existing hooks, please contact us to discuss
the matter.
