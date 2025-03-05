# Add a command to store the results of command/query execution

While participating in a support escalation on a Kubernetes cluster, it
struck me how tedious and error-prone it was to execute queries across
nodes on the cluster and copy the results out for further analysis.

TPA has some pieces that could make this easier for its clusters:

* `tpaexec cmd` executes ad-hoc commands (including via `-m script`),
  and `tpaexec playbook` executes playbooks.

* `tpaexec test` and other commands like `archive-logs` already know how
  to copy things from the instances and store them in local directories

We could put these together into a slightly different form and provide a
command like the following:

    tpaexec execute mycluster \
        [--commands-from … | --queries-from … | --script …]

This would execute the given input on all applicable instances (and we
could support `--hosts role_xyz:!role_pqr` as well), and create local
directories in the style of `tpaexec test` and store the output there,
with unambiguous hostnames and timestamps.

Or perhaps we could have separate commands:

    tpaexec execute-script mycluster xyz.sh
    tpaexec execute-queries mycluster xyz.sql

(We don't need to do anything for playbooks, because `tpaexec playbook`
is good enough already.)
