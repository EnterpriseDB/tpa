#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

import base64
import hashlib
from hmac import HMAC
from ansible.errors import AnsibleFilterError

try:
    from passlib.hash import scram

    HAVE_PASSLIB = True
except ImportError:
    HAVE_PASSLIB = False

# Returns ``'md5' || md5_hex( password || username ))`` as computed by
# pg_md5_encrypt() in src/common/md5.c


def md5_password(password, username):
    return (
        "md5%s"
        % hashlib.md5(password.encode("utf-8") + username.encode("utf-8")).hexdigest()
    )


# Returns ``SCRAM-SHA-256$<iteration count>:<salt>$<StoredKey>:<ServerKey>`` as
# computed by scram_build_verifier() in src/common/scram-common.c


def scram_password(password, salt=None, rounds=4096):
    s = scram.using(rounds=rounds, salt=salt, algs="sha-1,sha-256").hash(password)

    (salt, rounds, SaltedPassword) = scram.extract_digest_info(s, "sha-256")

    ClientKey = HMAC(
        SaltedPassword, "Client Key".encode("ascii"), hashlib.sha256
    ).digest()
    ServerKey = HMAC(
        SaltedPassword, "Server Key".encode("ascii"), hashlib.sha256
    ).digest()
    StoredKey = hashlib.sha256(ClientKey).digest()

    return "%s$%s:%s$%s:%s" % (
        "SCRAM-SHA-256",
        rounds,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(StoredKey).decode("ascii"),
        base64.b64encode(ServerKey).decode("ascii"),
    )


# Takes a password_encryption value, a password, and a username (required only
# if password_encryption == 'md5') and returns a string that is suitable for use
# as the PASSWORD in CREATE USER commands.


def encrypted_password(
    password_encryption, password, username=None, existing_password=None
):
    if password_encryption == "md5":
        return md5_password(str(password), username)
    elif password_encryption == "scram-sha-256":
        salt = None
        rounds = None

        if not HAVE_PASSLIB:
            raise AnsibleFilterError(
                "|encrypted_password requires passlib (did you run `tpaexec setup`?)"
            )

        if existing_password and existing_password.startswith("SCRAM-SHA-256$"):
            (_, info, _) = existing_password.split("$", 2)
            (rounds, b64salt) = info.split(":", 1)
            salt = base64.b64decode(b64salt)
            rounds = int(rounds)

        return scram_password(str(password), salt=salt, rounds=rounds)

    raise AnsibleFilterError(
        "|encrypted_password does not recognise password_encryption scheme %s"
        % password_encryption
    )


class FilterModule(object):
    def filters(self):
        return {
            "encrypted_password": encrypted_password,
        }
