#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

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

    MSG = "An error was encountered during execution of tpaexec configure"

    @property
    def message(self):
        return self.MSG


class PlatformError(TPABaseException):
    """Error condition in TPA platform use."""

    MSG = "An error occurred during Platform processing"
