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
# TPAexec 23.18.18
tpaexec=./tpaexec
TPA_DIR=/opt/EDB/TPA
PYTHON=/opt/EDB/TPA/tpa-venv/bin/python3 (v3.7.3, venv)
TPA_VENV=/opt/EDB/TPA/tpa-venv
ANSIBLE=/opt/EDB/TPA/tpa-venv/bin/ansible (v2.9.27)
Validation: e05e5302cd357b8ddbb042b7591bf66dfa283213ccbe5073b2cff3c783be1310 [OK]
```
