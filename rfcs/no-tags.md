# Replacing the use of tags in TPA

TPA currently uses tags throughout the code, in a fairly systematic way
(e.g., packaging tasks are tagged with "pkg", tasks that restart things
are tagged with "restart").

There are several problems with the use of tags in general, and with
their use by TPA in particular:

1. Ansible provides little control over how tags are applied to tasks,
   and how they are selected or omitted for execution. You can't use
   complex specifications like `--tags a,b,c --skip-tags p,q,r` to
   control which tasks are executed at a fine-grained level.

2. Tags are a constant maintenance burden, in terms of getting the
   tagging right (especially given the need to set `tags: always` on
   outer includes if there may be any always-tagged tasks somewhere in
   the included files). They just get cargo-culted from existing tasks,
   and mostly pass through review without careful consideration, because
   they don't obviously break anything.

3. 2ndQuadrant/ansible contains a fix for the --skip-tags misbehaviour
   in Ansible whereby any tasks tagged with [x, always] are skipped by
   specifying `--skip-tags x`; in many cases, the "x" tag is inherited
   from the apply of some outer include, and can't be avoided.

   This is not a matter of "informed consent". It is not safe to run a
   deploy using `--skip-tags` where always-tagged tasks can be skipped.
   Therefore, it is not possible to use --skip-tags when using Ansible.

Nevertheless, it would be useful to have fine-grained control over the
execution of roles and tasks in TPA.

## Proposal

First, we remove all "tags: …" specifications in TPA.

Next, make it possible to run:

    tpaexec deploy mycluster -e select_tasks="…"

The new select_tasks variable comprises one or more clauses separated by
commas. The syntax of individual clauses is discussed below.

Next, roles/init parses `select_tasks` and converts the clauses into
settings under a `selected_tasks` hash.

Individual roles, tasks, and includes can then decide whether to
continue execution or not based on any combination of settings under
`selected_tasks`.

For example, you could specify `!restart` to prevent deploy from ever
restarting any service. Or perhaps you could use `!restart:postgres` to
prevent only Postgres restarts.

With this arrangement, there would be no tasks tagged "always" to be
mistakenly skipped, but we could still specify which tasks to execute
with a fair degree of precision.
