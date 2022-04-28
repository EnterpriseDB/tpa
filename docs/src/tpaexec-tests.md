# TPAexec custom tests

You can easily define in-depth tests specific to your environment and
application to augment TPAexec's [builtin tests](tpaexec-test.md).

We strongly recommend writing tests for any tasks, no matter how simple,
that you would run on your cluster to reassure yourself that everything
is working as you expect. Having a uniform and repeatable way to run
such tests ensures that you don't miss out on anything important,
whether you're dealing with a crisis or just doing routine cluster
management.

If you write tests that target cluster instances by their configured
role (or other properties), you can be sure that all applicable tests
will be run on the right instances. No need to look up or remember how
many replicas to check the replication status on, nor which servers are
running pgbouncer, or any other such details that are an invitation to
making mistakes when you are checking things by hand.

Tests must not make any significant changes to the cluster. If it's not
something you would think of doing on a production server, it probably
shouldn't be in a test.

## Quickstart

* Create `tests/mytest.yml` within your cluster directory
* Run `tpaexec test /path/to/cluster mytest`

You can also create tests in some other location and use them across
clusters with the `--include-tests-from /other/path` option to
`tpaexec test`.

(Run `tpaexec help test` for usage information.)

## Example

Here's how to write a test that is executed on all Postgres instances
(note `hosts: role_postgres` instead of `hosts: all`).

You can use arbitrary Ansible tasks to collect information from the
cluster and perform tests. Just write tasks that will fail if some
expectation is not met (`assert`, `fail … when`, etc.).

```yaml
---
- name: Perform my custom tests
  hosts: role_postgres
  tasks:

  # Always start with this
  - include_role:
      name: test
      tasks_from: prereqs.yml

  # Make sure that the PGDATA/PG_VERSION file exists. (This is just a
  # simplified example, not something that actually needs testing.)
  - name: Perform simple test
    command: "test -f {{ postgres_data_dir }}/PG_VERSION"
    become_user: "{{ postgres_user }}"
    become: yes

  - name: Run pg_controldata
    command: >
      {{ postgres_bin_dir }}/pg_controldata {{ postgres_data_dir }}
    register: controldata
    become_user: "{{ postgres_user }}"
    become: yes

  # Write output to clusterdir/$timestamp/$hostname/pg_controldata.txt
  - name: Record pg_controldata output
    include_role:
        name: test
        tasks_from: output.yml
    vars:
      output_file: pg_controldata.txt
      content: |
        {{ controldata.stdout }}
```

You can use the builtin `output.yml` as shown above to record arbitrary
test output in a timestamped test directory in your cluster directory.

Each test must be a complete Ansible playbook (i.e., a list of plays,
not just a list of tasks). It will be imported and executed after the
basic TPAexec setup tasks.

## Destructive tests

Tests should not, by default, make any significant changes to a cluster.
(Even if they do something like creating a table to test replication,
they must be careful to clean up after themselves.)

Any test that makes changes to a cluster that would be unacceptable on a
production cluster MUST be marked as `destructive`. These may be tests
that you run only in development, or during the initial cluster "burn
in" process.

You can define "destructive" tests by setting `destructive: yes` when
including `prereqs.yml` in your test:

```yaml
- hosts: …
  tasks:
  - include_role:
      name: test
      tasks_from: prereqs.yml
    vars:
      destructive: yes
```

If someone then runs `tpaexec test /path/to/cluster mytest`, they will
get an error asking them to confirm execution using the
`--destroy-this-cluster` option.

(Note: using `--destroy-this-cluster` signifies an awareness of the risk
of running the command. It does not guarantee that the test will
actually destroy the cluster.)
