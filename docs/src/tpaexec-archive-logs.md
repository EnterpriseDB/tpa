# tpaexec archive-logs

To create a log directory and archive logs from instances, run

```bash
tpaexec archive-logs <cluster-dir>
```

This will create a logs/YYYYMMDDHHMMss/ directory in your cluster directory
and download a tar.gz archive of all the files under /var/log on each instance
in the cluster into a separate directory.

## Prerequisites

If you have an existing cluster you can run `tpaexec archive-logs`
immediately. But if you are configuring a new cluster, you must at least
[provision](tpaexec-provision.md) the cluster. You will get more logs if
you also [deploy](tpaexec-deploy.md) the cluster.

## Quickstart

```bash
[tpa]$ tpaexec archive-logs ~/clusters/speedy

PLAY [Prepare local host archive] *******************************************

TASK [Collect facts] ********************************************************
ok: [localhost]

TASK [Set time stamp] *******************************************************
ok: [localhost]

TASK [Create local log archive directory] ***********************************
changed: [localhost]

PLAY [Archive log files from target instances] ******************************

...

TASK [Remove remote archives] ***********************************************
changed: [kinship]
changed: [khaki]
changed: [uncivil]
changed: [urchin]

PLAY RECAP ******************************************************************
khaki                      : ok=3    changed=3    unreachable=0    failed=0
kinship                    : ok=3    changed=3    unreachable=0    failed=0
localhost                  : ok=3    changed=1    unreachable=0    failed=0
uncivil                    : ok=3    changed=3    unreachable=0    failed=0
urchin                     : ok=3    changed=3    unreachable=0    failed=0
```

You can append `-v`, `-vv`, etc. to the command if you want more verbose output.

## Generated files

You can find the logs for each instance under the cluster directory:

```bash
~/clusters/speedy/logs/
`-- 220220306T185049
    |-- khaki-logs-20220306T185049.tar.gz
    |-- kinship-logs-20220306T185049.tar.gz
    |-- uncivil-logs-20220306T185049.tar.gz
    `-- urchin-logs-20220306T185049.tar.gz
```

Archive contents example:

```bash
khaki-logs
|-- anaconda
|   |-- anaconda.log
|   |-- dbus.log
|   |-- dnf.librepo.log
|   |-- hawkey.log
|   |-- journal.log
|   |-- ks-script-ipdkisn0.log
|   |-- ks-script-jr03uzns.log
|   |-- ks-script-mh2iidvh.log
|   |-- lvm.log
|   |-- packaging.log
|   |-- program.log
|   |-- storage.log
|   |-- syslog
|   `-- X.log
|-- btmp
|-- dnf.librepo.log
|-- dnf.log
|-- dnf.rpm.log
|-- hawkey.log
|-- lastlog
|-- private
|-- tpaexec.log
`-- wtmp
```
