Guidelines for contributors
===========================

## Git configuration

Please make sure that your name and email address are set in your
`~/.gitconfig` (or `.git/config`) before committing any changes:

```
[user]
  name = Preferred Name
  email = first.last@enterprisedb.com
```

## Commit messages

Please use the conventional commit message format: a single-line summary
of the change, optionally followed by a blank line and then any number
of lines of additional free-form commentary.

### Summary line

Initial capital, preferably <60 characters, no trailing period.

Ideally written in imperative mood (e.g., "Document …", "Simplify …",
"Remove …", "Change …", "Fix …").

A leading tag may sometimes be helpful to clearly communicate the scope
of a particular change, e.g., "zabbix: Fix .pgpass generation" or
"Testing: Increase default failure timeouts". Use your judgement.

### Github metadata

Please do **not** @mention any users in commit messages (to avoid having
Github spam them with notifications when the commit is rebased, etc.).

References to issues in `#nnn` form will be converted to links in the
Github UI. If your commit closes one or more open issue on Github, put
a "Closes #nnn" line for each issue at the end of your commit message.

```
Closes #123
```
