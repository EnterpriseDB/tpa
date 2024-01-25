# Description

This repository contains a workflow named `Build release notes for a new version`,
which is implemented in `.github/workflows/relnotes.yml`.

The purpose of that workflow is to automatize the generation of release notes when
releasing a new version of a software.

That way we expect to reduce the releasing time. The idea is that developers
write and review the release notes through YAML files during development. When it
is time for releasing, then we should just "hit a button" to get the release notes
of the project updated accordingly. After that it is just a matter of reviewing
and merging a PR that was automatically created, and proceed with the release
process.

Refer to [YAML file format](#yaml-file-format) section for more details about
the expected structure of the YAML files.

Refer to [Installing the workflow/script](#installing-the-workflowscript) for
details about how to install this workflow in your repository.

**Note:** The files under `release_notes` directory, and the actual `relnotes.md`
file in this repository, are shared as an example. If you run the workflow in this
repository pointing to that file and directory, you can see a sample PR being
created.

## `relnotes.yml` workflow

As mentioned above, this repository contains an workflow file named `relnotes.yml`.

You can find more specific information in the following sub-sections.

### Inputs

The workflow is a dispatchable workflow that accepts the following arguments:

- `version`: version that is being released. It is any string that names the version.
- `date`: release date in the format `yyyy-mm-dd`.
- `base_branch`: this is the base branch of this repository. That branch should contain
a set of relase note files in YAML format as well as the actual release notes file
that is delivered by the project.
- `source_directory`: after checking out this repository on `base_branch`, `source_directory`
should be the relative path to a directory containing the release notes YAML files.
- `output_file`: after checking out this repository on `base_branch`, `output_file`
should be the relative path to the release notes file to be updated.
- `git_user_name`: GitHub username to be used in commit messages.
- `git_user_email`: GitHub email to be used in commit messages.

### Steps

The workflow roughly performs these steps:

1. Checkout this repo on ref `base_branch`.
2. Create a new branch named `release_notes/VERSION` on top of `base_branch`,
where `VERSION`. is given by `version`.
3. Run the `update_relnotes.py` script to amend the project release notes file.
Refer to [`update_relnotes.py` script](#update-relnotespy-script) for more details.
4. Remove all release notes YAML files from `source_directory`.
5. Create a PR from `release_notes/VERSION` to `base_branch`.

## `update_relnotes.py` script

This Python script is in charge of reading all release notes YAML files and then
of using that information to update the actual release notes file of the project.

It will basically insert a section in the middle of an existing release notes file.

It copies all the heading description that is contained in the release notes file,
then writes a section about the current version being released, with its release
notes, and then copies the remaining content of the original release noets file.

If the script faces any kind of issues it will exit immediately with a fatal
message.

### Inputs

The script requires the following arguments:

- `-s`/`--source-directory`: path to a directory containing the release notes in
YAML format
- `-o`/`--output-file`: path to the release notes file of the project, which this
script should amend based on the YAML files.
- `-v`/`--version`: the name of the version that is being released for the software.
- `-d`/`--date`: the release date of the new version, in the format `yyyy-mm-dd`.

### YAML file format

The script expects to find one or more YAML files under `--source-directory`.
Each of these files is one release note that will be written to `--output-file`.

The YAML file content can contain a list of items, each item with the following
fields:

- `summary`: a short description to be used as the title of the release note. It
should be written in markdown syntax.
- `description`: a longer description to be used as the body of the release note.
It should be written in markdown syntax. This is optional.
- `type`: type of the release note. Should be one among:
    - `notable_change`: a bigger impact change.
    - `minor_change`: some punctual change.
    - `bugfix`: bugfix patch.`
- `jira_tickets`: a list of Jira tickets related with this release note. This is
optional.
- `support_tickets`: a list of Support tickets related with this release note. This
is optional.

**Note:** at least one ticket should exist in `jira_tickets` + `support_tickets`
resulting set.

This is an example of an YAML file:

```yaml
- summary: Support deploying to SLES 15
  description: |
    Pass `--os SLES` to `tpaexec configure` to deploy to SLES.

    The M1 and PGD-Always-ON architectures are supported on all platforms.

    Creation of local repositories (and therefore air-gapped installation)
    is not yet supported on SLES
  type: notable_change
  jira_tickets:
  - TPA-101
- summary: Build packages to run TPA on SLES 15
  type: minor_change
  jira_tickets:
  - TPA-101

```

### Example

Assume you had the following content in your release notes file:

```markdown
# TPA release notes

© Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

## v23.17 (2023-05-10)

### Notable changes

- TPA-383 Require --pgd-proxy-routing global|local to be specified at
  configure time for PGD-Always-ON clusters

  This option determines how PGD-Proxy instances will route connections
  to a write leader. Local routing will make every PGD-Proxy route to
  a write leader within its own location (suitable for geo-sharding
  applications). Global routing will make every proxy route to a
  single write leader, elected amongst all available data nodes across
  all locations (i.e., all pgd-proxy instances will be attached to the
  top-level node group).

  (This option entirely replaces the earlier --active-locations option,
  and also resolves some problems with the earlier top-level routing
  configuration.)

- TPA-102 Support deploying to Ubuntu 22.04

  TPA can now provision and deploy nodes running Ubuntu 22.04 ("Jammy
  Jellyfish") on either docker containers or AWS.

### Minor changes

- Update AWS AMIs for RHEL7 and RHEL8

- Documentation improvements

### Bugfixes

- TPA-404 Don't remove groups from an existing postgres user

- Fix `Failed to commit files to git: b''` error from `tpaexec configure`;
  if the commit fails, the correct error message will now be shown

- TPA-416 Correctly sanitise subgroup names

  If subgroup names contain upper-case letters, lowercase them rather
  than replacing them with underscores.

- TPA-415 Ensure Postgres is correctly restarted, if required, after
  CAMO configuration

- TPA-400 Ensure etcd config changes are idempotent

  Enforce an ordering on the list of etc nodes and create data files
  with correct permissions, so that etcd doesn't get restarted
  unnecessarily on second and subsequent deployments.
```

And assume that you had a `--source-directory` with a single file named `TPA-101.yml`,
with the content that was described in [#YAML file format](#yaml-file-format).

If you run the script with `--version` as `v23.18` and `--date` as `2023-07-26`,
then you would obtain the following diff in the release notes file:

```diff
diff --git a/relnotes.md b/relnotes.md
index 6541ba4..f45cfc1 100644
--- a/relnotes.md
+++ b/relnotes.md
@@ -2,6 +2,27 @@

 © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

+## v23.18 (2023-07-26)
+
+### Notable changes
+
+- Support deploying to SLES 15
+
+  Pass `--os SLES` to `tpaexec configure` to deploy to SLES.
+
+  The M1 and PGD-Always-ON architectures are supported on all platforms.
+
+  Creation of local repositories (and therefore air-gapped installation)
+  is not yet supported on SLES
+
+  References: TPA-101.
+
+### Minor changes
+
+- Build packages to run TPA on SLES 15
+
+  References: TPA-101.
+
 ## v23.17 (2023-05-10)

 ### Notable changes
```

## Installing the workflow/script

If you want to install this workflow in your project you should just copy the
folder `.github/workflows/relnotes` and the file `.github/workflows/relnotes.yml`
from this repository to your repository.

### Customizing the script

The script for updating release notes file was created following the conventions
of the TPA project release notes file.

If you want to change the processing logic you will have to ultimately change
the implementation of files under `.github/workflows/relnotes/relnotes` directory.

These are some keypoints for changes:

* Change enum values of class `RelNoteType`: TPA creates the sections `Notable Changes`,
`Minor Changes` and `Bugfixes` when categorizing release notes of a given version.
If your project uses a different semantic, you would need to change the enum values
of that class, and possibly its `to_markdown` method to write a markdown content
that respects the structure of your release notes file/handle plurals properly.
* Change method `to_markdown` of `RelNote` class: you can generate a markdown content
corresponding to the `RelNote` attributes the way you want. The implementation of
that method in this repository also follows the TPA convention.
* Change logic on how to find the place to amend the release notes file: that logic
is implemented in method `update_release_notes` of class `RelNotesHandler`. The logic
implemented in this repository follow the TPA convention for the release notes file,
which creates a new level 2 header for each version. So we find that pivot line when
modifying the release notes markdown file, and prepend that with the release notes
of the new version. Modify according to your needs.
