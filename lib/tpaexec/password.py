#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

import os
import sys
import keyring
import secrets
import string
from tpaexec.architecture import KEYRING_SUPPORTED_BACKENDS

APPROVED_SYMBOLS = "!@#%^&*()_+"
KEYRING_PREFIX = "TPA_"
VAULT_PASS_RELATIVE_PATH = "vault/vault_pass.txt"
NO_KEYRING_ERROR_MSG = """Could not find compatible keyring backend,
ensure that you have a compatible backend for python keyring module
or use keyring_backend: legacy in config.yml"""

def generate_password():
    """
    Generates a password for use within TPA.

    This function takes no arguments and returns a string containing a password
    that is suitable for use as a database password, or as needed elsewhere for
    the cluster.
    """

    charset = string.ascii_letters + string.digits + APPROVED_SYMBOLS
    return ''.join(secrets.choice(charset) for i in range(32))


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
        exit(1)
    except keyring.errors.NoKeyringError:
        print(NO_KEYRING_ERROR_MSG)
        exit(1)


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
            exit(3)

    elif keyring_backend in KEYRING_SUPPORTED_BACKENDS:
        try:
            password = keyring.get_password(KEYRING_PREFIX + cluster_name, password_name)
        except keyring.errors.NoKeyringError:
            print(NO_KEYRING_ERROR_MSG)
            exit(1)
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
    cluster_name = os.path.basename(os.path.abspath(cluster_dir))
    if (
        keyring_backend in KEYRING_SUPPORTED_BACKENDS
        and keyring_backend != "legacy"
    ):
        try:
            if keyring.get_password(KEYRING_PREFIX + cluster_name, password_name) is None:
                return False
        except keyring.errors.NoKeyringError:
            return False

    elif (
        keyring_backend is None or keyring_backend == "legacy"
    ) and not os.path.exists("/".join([cluster_dir, VAULT_PASS_RELATIVE_PATH])):
        return False
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
    # nothing to do but keeping the example for later use.
    if keyring_backend in KEYRING_SUPPORTED_BACKENDS:
        if keyring_backend == "system":
            pass