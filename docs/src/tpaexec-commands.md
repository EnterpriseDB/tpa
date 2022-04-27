# TPAexec custom commands

You can define custom commands that perform tasks specific to your
environment on the instances in a TPAexec cluster.

You can use this mechanism to automate any processes that apply to your
cluster. These commands can be invoked against your cluster directory,
like any built-in cluster management command. Having a uniform way to
define and run such processes reduces the likelihood of errors caused by
misunderstandings and operator error, or process documentation that was
correct in the past, but has drifted away from reality since then.

Writing Ansible playbooks means that you can implement arbitrarily
complex tasks; following the custom command conventions means you can
take advantage of various facts that are set based on your config.yml
and the cluster discovery tasks that TPAexec performs, and not have to
think about details like connections, authentication, and other basic
features.

This makes it much easier to write resilient, idempotent commands in a
way that ad-hoc shell scripts (could be, but) usually aren't.

## Quickstart

* Create `commands/mycmd.yml` within your cluster directory
* Run `tpaexec mycmd /path/to/cluster`

## Example

Here's an example of a command that runs a single command on all
instances in the cluster. Depending on the use-case, you can write
commands that target different hosts (e.g., `hosts: role_postgres` to
run only on Postgres instances), or run additional tasks and evaluate
conditions to determine exactly what to do.

```yaml
---
# Always start with this
- import_playbook: "{{ tpa_dir }}/architectures/lib/init.yml"
  tags: always

- name: Perform custom command tasks
  hosts: all
  tasks:
  - name: Display last five lines of syslog
    command: tail -5 /var/log/syslog
    become_user: root
    become: yes
```
