# TPA, Ansible, and sudo

TPA uses Ansible with sudo to execute tasks with elevated privileges
on target instances. 
It's important to understand how Ansible uses sudo (which isn't specific to TPA) 
and the consequences to systems managed
with TPA.

TPA needs root privileges;

* To install packages (required packages using the operating system's
  native package manager and optional packages using pip)
* To stop, reload, and restart services (that is, Postgres, repmgr, efm, etcd,
  haproxy, pgbouncer, and so on)
* To perform a variety of other tasks (such as gathering cluster facts,
  performing switchover, and setting up cluster nodes)

TPA also must be able to use sudo. You can make it ssh in as root
directly by setting `ansible_user: root`, but it still uses sudo to
execute tasks as other users (for example, postgres).

## Ansible sudo invocations

When Ansible runs a task using sudo, you see a process on the
target instance that looks something like this:

```
/bin/bash -c 'sudo -H -S -n  -u root /bin/bash -c \
  '"'"'echo BECOME-SUCCESS-kfoodiiprztsyerriqbjuqhhbemejgpc ; \
  /usr/bin/python2'"'"' && sleep 0'
```

Users who were expecting something like `sudo yum install -y xyzpkg`
are often surprised by this. By and large, most tasks in Ansible
invoke a Python interpreter to execute Python code rather than
executing recognizable shell commands. (Playbooks can execute `raw`
shell commands, but TPA uses such tasks only to bootstrap a Python
interpreter.)

Ansible modules contain Python code of varying complexity, and an
Ansible playbook isn't just a shell script written in YAML format.
There's no way to “extract” shell commands that do the same thing
as executing an arbitrary Ansible playbook.

One significant consequence of how Ansible uses sudo is that [privilege
escalation must be general](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html#privilege-escalation-must-be-general). It isn't possible
to limit sudo invocations to specific commands in `sudoers.conf`,
as some administrators are used to doing. Most tasks just invoke Python.
You could have restricted sudo access to Python if it weren't
for the random string in every command. However, once Python is running as root,
there's no effective limit on what it can do anyway.

Executing Python modules on target hosts is how Ansible works.
None of this is specific to TPA, and these considerations
apply equally to any other Ansible playbook.

## Recommendations

* Use SSH public-key-based authentication to access target instances.

* Allow the SSH user to execute sudo commands without a password.

* Restrict access by time rather than by command.

TPA needs access only when you're first setting up your cluster or
running `tpaexec deploy` again to make configuration changes, for example,
during a maintenance window. Until then, you can disable its access
entirely, which is a one-line change for both ssh and sudo.

During deployment, everything Ansible does is generally predictable
based on what the playbooks are doing and the parameters you provide.
Each action is visible in the system logs on the target instances
as well as in the Ansible log on the machine where tpaexec runs.

Ansible's focus is less to impose fine-grained restrictions on the
actions you can execute and more to provide visibility into what it does
as it executes. Thus elevated privileges are better assigned and managed
by time rather than by scope.

## SSH and sudo passwords

We strongly recommend setting up passwordless SSH key authentication
and passwordless sudo access. However, it's possible to use passwords too.

If you set `ANSIBLE_ASK_PASS=yes` and `ANSIBLE_BECOME_ASK_PASS=yes`
in your environment before running tpaexec, Ansible prompts you to
enter a login password and a sudo password for the remote servers. It
then negotiates the login/sudo password prompt on the remote server
and sends the password you specify, which makes your playbooks take
noticeably longer to run.

We don't recommend this mode of operation because it's a more
effective security control to completely disable access through a
particular account when not needed than to use a combination of
passwords to restrict access. Using public key authentication for ssh
provides an effective control over who can access the server, and it's
easier to protect a single private key per authorized user than it is to
protect a shared password or multiple shared passwords. Also, if you
limit access at the ssh/sudo level to when it's required, the passwords
don't add any extra security during your maintenance window.

## sudo options

To use Ansible with sudo, don't set `requiretty` in `sudoers.conf`.

If needed, you can change the sudo options that Ansible uses
(`-H -S -n`) by setting either:
- `become_flags` in the `[privilege_escalation]` section of `ansible.cfg`
- `ANSIBLE_BECOME_FLAGS` in the environment
- `ansible_become_flags` in the inventory 

All three methods are equivalent, but change
the sudo options only if there's a specific need to do so. The defaults
were chosen for good reasons. For example, removing `-S -n` will cause
tasks to time out if passwordless sudo is incorrectly configured.

## Logging

For playbook executions, the sudo logs show mostly invocations of
Python, just as it shows only an invocation of bash when
`sudo -i` is used.

For more detail, the syslog shows the exact arguments to each module
invocation on the target instance. For a higher-level view of why that
module was invoked, the `ansible.log` on the controller shows what that
task was trying to do, and the result.

If you want even more detail or an independent source of audit data,
you can run auditd on the server and use the SELinux log files. You can
get still more fine-grained syscall-level information from bpftrace/bcc.
(For example, opensnoop shows every file opened on the system, and execsnoop
shows every process executed on the system.) You can do any or all of
these things, depending on your needs, with the obvious caveat of
increasing overhead with increased logging.

## Local privileges

The
[installation instructions for TPA](INSTALL.md)
mention sudo only as shorthand for “run these commands as root somehow.”
Once TPA is installed and you've run `tpaexec setup`, TPA
doesn't require elevated privileges on the local machine. (But
if you use Docker, you must run tpaexec as a user that belongs to a
Unix group that has permission to connect to the Docker daemon.)
