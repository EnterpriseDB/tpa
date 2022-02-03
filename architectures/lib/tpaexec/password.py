#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from passlib import pwd


def generate_password():
    """
    Generates a password for use within TPAexec.

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
