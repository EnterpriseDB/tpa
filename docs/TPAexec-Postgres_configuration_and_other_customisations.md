---
title: TPAexec - Postgres configuration and other customisations
version: 1.0
date: 01/June/2018
author: Craig Alsop
copyright-holder: 2ndQuadrant Limited
copyright-years: 2018
toc: true
---

TPAexec - Postgres configuration and other customisations
==================

© Copyright 2ndQuadrant, 2018. Confidential property of 2ndQuadrant; not for public release.

### Postgres postgresql.conf configuration variables

These can be configured by TPAexec at build time by setting the relevant parameters as node vars in the **$TPA_HOME/clusters/\<clustername>/config.yml** file - as in this excerpt:

```
instances:
    - node: 1
      Name: lab-primary
      type: t2.micro
      region: eu-central-1
      subnet: 10.33.243.0/24
      volumes:
            device_name: /dev/xvdb
            volume_type: gp2
            volume_size: 32
            vars:
              volume_for: postgres_data
      tags:
        role:
          - primary
        backup: lab-backup
      vars:
        work_mem: 18MB
        max_connections: 222
        shared_buffers: '64MB'
```

Here, we see **work_mem**, **max_connections** & **shared_buffers** are all being defined - note that these should be defined as **\<variable>: \<value>**. To see what Postgres variables are possible to set, either read the documentation for the relevant Postgres version, or look in **\$PGDATA/postgresql.conf** on a Postgres server. 

During the deploy phase, TPAexec creates a directory on each Postgres node which contains files with settings which override those set in **\$PGDATA/postgresql.conf**. This directory conf.d is included as the last line in \$PGDATA/postgresql.conf by the setting:

```
include_dir = 'conf.d'
```

and is created in the $PGDATA directory (**/opt/postgres/data** by default).

Multiple files within the include directory are processed in file name order (according to C locale rules, i.e. numbers before letters, and uppercase letters before lowercase ones) - this means that only the last setting encountered for a particular parameter while the server is reading configuration files will be used. 

```
[postgres-server]$ ls $PGDATA/conf.d
0000-tpa.conf          1111-extensions.conf                9999-override.conf
0001-tpa_restart.conf  8888-shared_preload_libraries.conf
```

Settings which can be dynamically set are written during the TPAexec deploy phase to **0000-tpa.conf** and settings which require a db restart are written to **0001-tpa_restart.conf**.

More information regarding default settings that TPAexec will use during deployment can be found under **$TPA_HOME/roles/postgres/config/templates** in files **tpa.conf.j2** & **tpa_restart.conf.j2**

```
[tpa-server]$ ls $TPA_HOME/roles/postgres/config/templates
extensions.conf.j2  pg_hba.conf.j2   settings.conf.j2  tpa_restart.conf.j2
override.conf.j2    pg_hba.lines.j2  tpa.conf.j2       variable.j2
```

#### Manual updates

Bearing these in mind, any manual updates after TPAexec deployment for settings that override **\$PGDATA/postgresql.conf** on any node should be made only to **\$PGDATA/conf.d/9999-override.conf** because any other file may get overwritten or overridden by subsequent settings at service start time. This is where you should configure any setting that requires persistence after reboot.

Any settings added to **9999-override.conf** should also be added to the relevant **config.yml** on the TPAexec server so that any rehydrate or subsequent build of the node will contain the most up-to-date setting.

### Postgres pg_hba.conf configuration variables

These are automatically generated during deploy phase by TPAexec and should not manually edited, as they are likely to get overridden.

------

### Other customisations

It is possible to set up many other customisations during the build process by adding post_tasks and handlers to the final play in **$TPA_HOME/clusters/\<clustername>/deploy.yml**.

In this snippet, designed to be part of a training lab, we create a user "student", add them to admin group, set password, allow them to ssh with just password authentication, update /etc/sudoers, and restart ssh service. 

*Disclaimer - allowing ssh access to Internet facing instances with just password authentication is a security risk, and shouldn't be enabled on any production system*.

```
- name: Ensure /etc/hosts is correct cluster-wide
  any_errors_fatal: True
  max_fail_percentage: 0
  become_user: root
  become: yes
  hosts: all
  roles:
    - role: sys/hosts
      tags: [sys, hosts]
  post_tasks:
    - user:
        state: present
        name: student
        shell: /bin/bash
        group: admin
# password and quoted hash are both on the same line
        password: "$6$cRmk8XVtYzS.52Hk$ISMY65gigtvdzeBs0nr7B66mx7BOLoWq7tjQ2hxOJ9r28fLkVo1RscMhW9t2ortjwWSi5EUq7pLmoL84AEpUl/"
    - name: Allow password auth
      lineinfile:
          path: /etc/ssh/sshd_config
          regexp: "^PasswordAuthentication"
          line: "PasswordAuthentication yes"
          state: present
      notify: Restart ssh
    - name: Add student to sudoers
# Fully quoted line because of the ': '. See the Gotchas in the YAML docs.
      lineinfile: "dest=/etc/sudoers line='student        ALL=(ALL)       NOPASSWD: ALL'"

  handlers:
  - name: Restart ssh
    service: name=ssh state=restarted
```

The hashed password is created by installing **passlib** and running the following commands: (at the password prompt enter the password to be hashed)

```
$ pip install passlib
$ python -c "from passlib.hash import sha512_crypt; import getpass; print sha512_crypt.using(rounds=5000).hash(getpass.getpass())"
Password:
$6$cRmk8XVtYzS.52Hk$ISMY65gigtvdzeBs0nr7B66mx7BOLoWq7tjQ2hxOJ9r28fLkVo1RscMhW9t2ortjwWSi5EUq7pLmoL84AEpUl/
```

In this manner, post_tasks can be used to configure and modify server files - see [user](http://docs.ansible.com/ansible/latest/modules/user_module.html#user-module) and [lineinfile](http://docs.ansible.com/ansible/latest/modules/lineinfile_module.html) for more information on how to use those particular modules. Information about all the current modules available for Ansible can be found [here](http://docs.ansible.com/ansible/latest/modules/list_of_all_modules.html) or just the system modules [here](http://docs.ansible.com/ansible/latest/modules/list_of_system_modules.html). The [shell](http://docs.ansible.com/ansible/latest/modules/shell_module.html#shell-module) module can be used to run commands on the nodes.

[^Information Classification: Confidential]: [ISP008] Information Classification Policy
