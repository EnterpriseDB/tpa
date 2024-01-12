#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

import os
import sys
import keyring
from tpaexec.architecture import KEYRING_SUPPORTED_BACKENDS
from passlib import pwd

KEYRING_PREFIX = "TPA_"
VAULT_PASS_RELATIVE_PATH = "vault/vault_pass.txt"


def generate_password():
    """
    Generates a password for use within TPA.

    This function takes no arguments and returns a string containing a password
    that is suitable for use as a database password, or as needed elsewhere for
    the cluster.
    """

    # We use passlib to generate a password using its "ascii_72" character set
    # ([a-zA-Z0-9#^%*!&/?$@]), which does not include any characters that would
    # cause problems when interpolating into a YAML string, i.e., [:'"{}\\].
    #
    # We ask passlib for a "secure" password, but that's currently only 56 bits
    # of (estimated) entropy, and gives us relatively short passwords, so we
    # specify a minimum length of 32 characters anyway.
    #
    # See https://passlib.readthedocs.io/en/stable/lib/passlib.pwd.html for more
    # details about the password generation.

    return pwd.genword(entropy="secure", length=32, charset="ascii_72")


def store_password(cluster_dir, password_name, password, keyring_backend):
    """Leverage the chosen keyring backend to store a password for the cluster

    Args:
        cluster_dir (string): path of the cluster the password belongs to.
        password_name (string): name of the password entry to store
        password (string): password to store
        keyring_backend (string): name of keychain backend used to store the password
    """
    cluster_name = os.path.basename(os.path.abspath(cluster_dir))
    _initialize_keyring(
        cluster_dir=cluster_dir,
        keyring_backend=keyring_backend,
    )

    try:
        keyring.set_password(
            KEYRING_PREFIX + cluster_name, username=password_name, password=password
        )
    except keyring.errors.PasswordSetError:
        print(
            f"Failed to store password: {password_name} in system {KEYRING_PREFIX + cluster_name}"
        )


def show_password(cluster_dir, password_name, keyring_backend):
    """Display a password stored into a keyring backend

    Args:
        cluster_dir (string): path of the cluster the password belongs to.
        password_name (string): name of the password entry to store
        keyring_backend (string): name of keychain backend used to store the password
    Returns:
        string: password value or None
    """
    _initialize_keyring(
        cluster_dir=cluster_dir,
        keyring_backend=keyring_backend,
    )
    cluster_name = os.path.basename(os.path.abspath(cluster_dir))

    # legacy plain text file.
    if keyring_backend is None or keyring_backend == "legacy":
        try:
            with open("/".join([cluster_dir, VAULT_PASS_RELATIVE_PATH])) as vault_file:
                return print(vault_file.read().strip("\n"))
        except IOError:
            print(
                f"Could not open the vault_file: {'/'.join([cluster_dir, VAULT_PASS_RELATIVE_PATH])}"
            )
            raise

    elif keyring_backend in KEYRING_SUPPORTED_BACKENDS:
        password = keyring.get_password(KEYRING_PREFIX + cluster_name, password_name)
        if password is None:
            sys.exit(
                f"""Could not find vault password in system keyring, please use --ask-vault-pass
or ensure entry:
service: {KEYRING_PREFIX + cluster_name}
username: {password_name}
exists with the correct vault password by running:
`tpaexec provision {cluster_dir}`
or
`keyring set {KEYRING_PREFIX + cluster_name} {password_name}`"""
            )
        return print(password)
    else:
        sys.exit(1)


def delete_password(cluster_dir, password_name, keyring_backend):
    """delete password from keyring backend

    Args:
        cluster_dir (string): path of the cluster the password belongs to.
        keyring_backend (string): name of keychain backend used to store the password
        password_name (string): name of the password entry to delete
    """
    _initialize_keyring(
        cluster_dir=cluster_dir,
        keyring_backend=keyring_backend,
    )

    cluster_name = os.path.basename(os.path.abspath(cluster_dir))
    if keyring_backend is None or keyring_backend == "legacy":
        os.remove("/".join([cluster_dir, VAULT_PASS_RELATIVE_PATH]))
    elif keyring_backend in KEYRING_SUPPORTED_BACKENDS:
        keyring.delete_password(KEYRING_PREFIX + cluster_name, password_name)


def exists(cluster_dir, password_name, keyring_backend):
    """Returns true if password already exists otherwise returns false

    Args:
        cluster_dir (string): path of the cluster the password belongs to.
        password_name (string): name of the password entry to store
        keyring_backend (string): name of keychain backend used to store the password

    Returns:
        _type_: _description_
    """
    _initialize_keyring(
        cluster_dir=cluster_dir,
        keyring_backend=keyring_backend,
    )
    cluster_name = os.path.basename(cluster_dir)

    if (
        keyring_backend in KEYRING_SUPPORTED_BACKENDS
        and keyring.get_password(KEYRING_PREFIX + cluster_name, password_name) is None
    ):
        return False
    elif (
        keyring_backend is None or keyring_backend == "legacy"
    ) and not os.path.exists("/".join([cluster_dir, VAULT_PASS_RELATIVE_PATH])):
        return False
    else:
        return True


def _initialize_keyring(cluster_dir, keyring_backend):
    """Prepare keyring module to use the selected backend

    Args:
        cluster_dir (string): path of the cluster the password belongs to.
        keyring_backend (string): name of keychain backend to initialize
    """
    # will start with keyring only and we will probably need more python module to
    # support more use case (hashicorp vault seems to have no good keyring
    # implementation and could require hvac module instead)

    # python keyring backend module supported
    # this will allow for other module to be used if needed.
    if keyring_backend in KEYRING_SUPPORTED_BACKENDS:
        if keyring_backend == "system":
            from keyring.backends.chainer import ChainerBackend

            keyring.set_keyring(ChainerBackend())
