# Uploading artifacts

You can define `artifacts` to create or copy files to target instances:

```yaml
cluster_vars:
  artifacts:
  - type: path
    path: /some/target/path
    state: directory
    owner: root
    group: root
    mode: 0755
  - type: file
    src: /host/path/to/file
    dest: /target/path/to/file
    owner: root
    group: root
    mode: 0644
  - type: archive
    src: example.tar.gz
    dest: /some/target/path
  - type: directory
    src: /host/path/a/
    dest: /target/path/b/
```

The following types are supported:

* Use `path` to create or remove and change the ownership or mode of
  files and directories (takes the same parameters as Ansible's `file`
  module, which it uses internally)

* Use `file` to copy a file from the controller and set the ownership
  and mode (uses `copy`)

* Use `archive` to extract files from an archive to a specified location
  (uses `unarchive`)

* Use `directory` to rsync a directory from the controller to target
  instances (uses `synchronize`)

The example shows one entry for each of the above artifact types, but
you can use these or any other parameters that the corresponding Ansible
module accepts.

Copying files and directories to target instances is a common-enough
need that this feature provides a convenient shortcut you can use
instead of writing a [custom hook](tpaexec-hooks.md).
