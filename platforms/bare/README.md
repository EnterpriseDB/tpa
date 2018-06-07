Bare-metal servers
------------------

Set «platform: bare» in config.yml

This platform is meant to support any server that is accessible via SSH,
including bare-metal servers as well as already-provisioned servers on
any cloud platform (including AWS).

You must define the IP address(es) and username for each target server:

```
instances:
  - node: …
    platform: bare
    private_ip: 192.0.2.1
    vars:
      ansible_user: xyzzy
```

The following actions must be performed for each target host:

1. Add the relevant SSH public key to ~user/.ssh/authorized_keys
2. Copy the SSH public host keys to known_hosts (or install the
   TPA-generated SSH host keys on the target).
3. Unless the remote user is root, it must be granted sudo access.
