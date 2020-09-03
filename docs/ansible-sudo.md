# TPAexec, Ansible, and sudo

TPAexec uses Ansible with sudo to execute tasks with elevated privileges
on target instances. This page explains how Ansible uses sudo (which is
in no way TPAexec-specific), and the consequences to systems managed
with TPAexec.

TPAexec needs root privileges to install packages, stop and restart
services, and a variety of other tasks. TPAexec also needs to be able to
use sudo. You can make it ssh in as root directly by setting
``ansible_user: root``, but it will still use sudo to execute tasks as
other users (e.g., postgres).

## Ansible sudo invocations

When Ansible runs a task using sudo, you will see a process on the
target instance that looks something like this:

```
/bin/bash -c 'sudo -H -S -n  -u root /bin/bash -c \
  '"'"'echo BECOME-SUCCESS-kfoodiiprztsyerriqbjuqhhbemejgpc ; \
  /usr/bin/python2'"'"' && sleep 0'
```

People who were expecting something like ``sudo yum install -y xyzpkg``
are often surprised by this. By and large, most tasks in Ansible will
invoke a Python interpreter to execute Python code, rather than
executing recognisable shell commands. (Playbooks may execute ``raw``
shell commands, but TPAexec uses such tasks only to bootstrap a Python
interpreter.)

Ansible modules contain Python code of varying complexity, and an
Ansible playbook is not just a shell script written in YAML format.
There is no way to “extract” shell commands that would do the same thing
as executing an arbitrary Ansible playbook.

There is one significant consequence of how Ansible uses sudo: it is not
possible to limit sudo invocations to specific commands in sudoers.conf,
as some administrators are used to doing. For one thing, most tasks will
just invoke python. You could have restricted sudo access to python if
it were not for the random string in every command—but once Python is
running as root, there's no effective limit on what it can do anyway.

Executing Python modules on target hosts is just the way Ansible works.
None of this is specific to TPAexec in any way, and these considerations
would apply equally to any other Ansible playbook.

## Recommendations

* Use SSH public key-based authentication to access target instances.

* Allow the SSH user to execute sudo commands without a password.

* Restrict access by time, rather than by command.

TPAexec needs access only when you are first setting up your cluster or
running ``tpaexec deploy`` again to make configuration changes, e.g.,
during a maintenance window. Until then, you can disable its access
entirely (a one-line change for both ssh and sudo).

During deployment, everything Ansible does is generally predictable
based on what the playbooks are doing and what parameters you provide,
and each action is visible in the system logs on the target instances,
as well as the Ansible log on the machine where tpaexec itself runs.

Ansible's focus is less to impose fine-grained restrictions on what
actions may be executed and more to provide visibility into what it does
as it executes, so elevated privileges are better assigned and managed
by time rather than by scope.

## SSH and sudo passwords

We *strongly* recommend setting up password-less SSH key authentication
and password-less sudo access, but it is possible to use passwords too.

If you set ``ANSIBLE_ASK_PASS=yes`` and ``ANSIBLE_BECOME_ASK_PASS=yes``
in your environment before running tpaexec, Ansible will prompt you to
enter a login password and a sudo password for the remote servers. It
will then negotiate the login/sudo password prompt on the remote server
and send the password you specify (which will make your playbooks take
longer to run).

We do not recommend this mode of operation because we feel it is a more
effective security control to completely disable access through a
particular account when not needed than to use a combination of
passwords to restrict access. Using public key authentication for ssh
provides an effective control over who can access the server, and it's
easier to protect a single private key per authorised user than it is to
protect a shared password or multiple shared passwords. Also, if you
limit access at the ssh/sudo level to when it is required, the passwords
do not add any extra security during your maintenance window.

## sudo options

To use Ansible with sudo, you must not ``requiretty`` in sudoers.conf.

If needed, you can change the sudo options that Ansible uses
(``-H -S -n``) by setting ``become_flags`` in the
``[privilege_escalation]`` section of ansible.cfg, or
``ANSIBLE_BECOME_FLAGS`` in the environment, or ``ansible_become_flags``
in the inventory. All three methods are equivalent, but please change
the sudo options only if there is a specific need to do so. The defaults
were chosen for good reasons. For example, removing ``-S -n`` will cause
tasks to timeout if password-less sudo is incorrectly configured.

## Logging

For playbook executions, the sudo logs will show mostly invocations of
Python (just as it will show only an invocation of bash when someone
uses ``sudo -i``).

For more detail, the syslog will show the exact arguments to each module
invocation on the target instance. For a higher-level view of why that
module was invoked, the ansible.log on the controller shows what that
task was trying to do, and the result.

If you want even more detail, or an independent source of audit data,
you can run auditd on the server and use the SELinux log files. You can
get still more fine-grained syscall-level information from bpftrace/bcc
(e.g., opensnoop shows every file opened on the system, and execsnoop
shows every process executed on the system). You can do any or all of
these things, depending on your needs, with the obvious caveat of
increasing overhead with increased logging.

## Local privileges

The
[installation instructions for TPAexec](INSTALL.md)
mention sudo only as shorthand for “run these commands as root somehow”.
Once TPAexec is installed and you have run ``tpaexec setup``, TPAexec
itself does not require elevated privileges on the local machine. (But
if you use Docker, you must run tpaexec as a user that belongs to a
group that is permitted to connect to the Docker daemon.)
