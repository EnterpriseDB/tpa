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

## Python formatting

All Python code must be formatted using
[Black](https://github.com/psf/black).

### Github metadata

Please do **not** @mention any users in commit messages (to avoid having
Github spam them with notifications when the commit is rebased, etc.).

References to issues in `#nnn` form will be converted to links in the
Github UI. If your commit closes one or more open issue on Github, put
a "Closes #nnn" line for each issue at the end of your commit message.

```
Closes #123
```

## Pull requests

Push your commits to a branch named `dev/short-description`; or if there
is an associated issue, `dev/nnn-short-description`. (One should be able
to get some idea of what the branch is about without needing to look up
the issue number.)

## New files

If you create any new files, please check existing files of the same
type to see if there's a header you need to copy. For example, a new
YAML file should start with the following text:

```
---

# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

```

(On the other hand, `.j2` templates that we expand and install on the
target do not contain a copyright message, but may need a warning to
avoid editing them by hand.)
