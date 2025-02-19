---
description: A command to output information about the TPA installation.
---


# tpaexec info

You can use the info command to output information about the TPA installation.
Providing this information is valuable for troubleshooting.

## Usage

* Run `tpaexec info`

### Subcommands
* `tpaexec info version`

    Displays current TPA version

* `tpaexec info platforms`

    Displays available deployment platforms

* `tpaexec info architectures`

    Displays available deployment architectures

* `tpaexec info platforms/<name>`

    Displays information about a particular platform

* `tpaexec info architectures/<name>`

    Displays information about a particular architecture

## Example Output

The `tpaexec info` command outputs the following:

```bash
# TPAexec 23.29
tpaexec=/opt/EDB/TPA/bin/tpaexec
TPA_DIR=/opt/EDB/TPA
PYTHON=/opt/EDB/TPA/tpa-venv/bin/python3 (v3.12.18, venv)
TPA_VENV=/opt/EDB/TPA/tpa-venv
ANSIBLE=/opt/EDB/TPA/tpa-venv/bin/ansible (v2.16.3)
Validated: ea844d1b90295597d080bbf824dbbc6954886cb54ffdb265c7c71b99bedee67b [OK]
```
