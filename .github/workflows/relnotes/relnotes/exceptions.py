"""Define exceptions that can occur when using this module."""


class RelNoteInvalidType(Exception):
    """Raise if :class:`RelNote` ``type`` is invalid."""

    pass


class RelNoteNoTicket(Exception):
    """Raised if :class:`RelNote` contains no Jira/Support tickets."""

    pass
