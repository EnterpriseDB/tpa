#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

"""Exception classes for tpaexec library."""


class TPABaseException(Exception):
    """
    Error condition in TPA execution.

    This is the default error (exception) class used when no other is defined.
    The MSG below is displayed on the CLI to the user.
    To make a more specific error message combine the use of a custom exception
    class which states the source of the error, such as the component of tpaexec
    library where the execution was taking place, with an error message.
    Use it in place of a print statement followed by `sys.exit(1)`:

        print('An error occurred during Architecture processing: Architecture unknown')
        sys.exit(1)

    Replace this with:

        raise ArchitectureError('Architecture unknown')

    """

    MSG = "An error occurred during execution of tpaexec configure"

    @property
    def message(self):
        return self.MSG


class PlatformError(TPABaseException):
    """Error condition in TPA platform use."""

    MSG = "An error occurred during Platform processing"


class ArchitectureError(TPABaseException):
    """Architecture error exception."""

    MSG = "An error occurred during Architecture processing"


class BDRArchitectureError(ArchitectureError):

    """BDR Architecture error exception class."""

    MSG = "An error occurred during BDR Architecture processing"


class ImagesArchitectureError(ArchitectureError):

    """Images Architecture error exception class."""

    MSG = "An error occurred during Images Architecture processing"


class AWSPlatformError(PlatformError):
    """Error condition in TPA AWS platform use."""

    MSG = "An error occurred during AWS Platform processing"


class DockerPlatformError(PlatformError):
    """Docker specific platform error exception."""

    MSG = "An error occurred during docker platform processing"


class NetError(TPABaseException):

    """Net error exception class."""

    MSG = "An error occurred during network address processing"


class TestCompilerError(TPABaseException):

    """Test Compiler error exception class."""

    MSG = "An error occurred during test compiling"


class PasswordReadError(TPABaseException):

    """Password reading error exception class."""

    MSG = "An error occurred while reading password"


class PasswordWriteError(TPABaseException):

    """Password writing error exception class."""

    MSG = "An error occurred while writing password"
