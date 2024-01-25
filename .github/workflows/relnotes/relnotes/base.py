"""Define base classes for dealing with release notes."""
from datetime import date
from enum import Enum
import os
from shutil import copyfile
from tempfile import NamedTemporaryFile
from textwrap import indent
from typing import Any, Callable, Dict, Iterator, List

from yaml import safe_load

from .exceptions import RelNoteInvalidType, RelNoteNoTicket


class RelNoteType(Enum):
    """Represent available types for a :class:`RelNote`.

    Can be one among:

        * ``NOTABLE_CHANGE``: a bigger impact change;
        * ``MINOR_CHANGE``: some punctual change;
        * ``BUGFIX``: bugfix patch.
    """

    NOTABLE_CHANGE = 1
    MINOR_CHANGE = 2
    BUGFIX = 3

    def to_markdown(self) -> str:
        """Generate markdown string corresponding to *self*.

        Create a level 3 header with type name in plural.

        :returns: markdown string representation of *self*.
        """
        plural = f"{self.name}{'' if self.name.endswith('E') else 'e'}s"
        return f"### {plural.replace('_', ' ').capitalize()}\n"


class RelNote:
    """Represent a release note parsed from a YAML file.

    :ivar summary: brief summary of the release note.
    :ivar description: broader description of the release note.
    :ivar type: type of the release note -- an instance of :class:`RelNoteType`
    :ivar tickets: a list of Support and/or Jira tickets that are related with
        this release note.
    """

    def __init__(self, *, summary: str, description: str = "", type: str,
                 jira_tickets: List[str] = [],
                 support_tickets: List[str] = []) -> None:
        """Instantiate a new :class:`RelNote` object with the given params.

        .. note::
            At least one item should exist from the union of *jira_tickets* and
            *support_tickets*.

        :param summary: brief summary of the release note.
        :param description: broader description of the release note, if any.
        :param type: type of the release note. Can be one among:

            * ``notable_change``: a bigger impact change;
            * ``minor_change``: some punctual change;
            * ``bugfix``: bugfix patch.

        :param jira_tickets: a list of 0 or more Jira tickets related to this
            release note.
        :param support_tickets: a list of 0 or more Support tickets related to
            this release note.

        :raises:
            :exc:`RelNoteInvalidType`: if *type* is invalid.
            :exc:`RelNoteNoTicket`: if concatenation of *jira_tickets* and
                *support_tickets* is an empty list.
        """
        self.summary = summary.strip()
        self.description = description.strip()
        try:
            self.type = RelNoteType.__members__[type.strip().upper()]
        except KeyError:
            raise RelNoteInvalidType(f"Type `{type}` is invalid. Use one among"
                                     " `notable_change`, `minor_change`, or "
                                     "`bugfix`.")
        self.tickets: List[str] = jira_tickets + support_tickets
        if len(self.tickets) == 0:
            raise RelNoteNoTicket("Concatenation of Jira tickets and Support "
                                  "tickets resulted into an empty list. At "
                                  "least one ticket is required.")

    def to_markdown(self, with_header: bool = False) -> str:
        """Generate markdown string corresponding to *self*.

        Creates an item for the release note.

        :param with_header: if we should also include the ``type`` header. Only
            call this with ``True`` if this release note is the first one in
            the list for a given ``type``.

        :returns: markdown string representation of *self*, optionally
            *with_header*.
        """
        return "{0}{1}{2}{3}\n".format(
            # 0
            f"{self.type.to_markdown()}\n"
            if with_header else "",
            # 1
            f"- {self.summary}",
            # 2
            f"\n\n{indent(self.description, '  ')}"
            if self.description else "",
            # 3
            f"\n\n  References: {', '.join(self.tickets)}.\n"
        )


class RelNotesHandler:
    """Handle release notes for a new version of a software.

    Provide means of reading and parsing release notes specs in YAML format,
    and use that to update the release notes file maintained by the project.

    In order to use this class:

        * Create an object of this class;
        * Call its :meth:`update_release_notes`.

    :ivar directory: path to a directory containing YAML files with relnote
        specs.
    :ivar file: path to release notes markdown file that is going be managed.
        Its encoding should be ``UTF-8``.
    :ivar version: the version that is being released.
    :ivar date: the release date.
    """

    def __init__(self, directory: str, file: str, version: str,
                 date: date, error: Callable[[str], None]) -> None:
        """Create a new instance of :class:`RelNotesHandler`.

        :param directory: path to a directory containing YAML files with
            release notes specs.
        :param file: path to release notes markdown file that is going be
            managed. Its encoding should be ``UTF-8``.
        :param version: the version that is being released.
        :param date: the release date.
        :param error: an error callback to be used when exceptions are faced
            on internal methods execution. It receives a single argument which
            is the error message, and should return ``None``. See
            :meth:`_get_relnotes_specs` and :meth:`_gather_relnotes`.
        """
        self.directory = directory
        self.file = file
        self.version = version
        self.date = date
        self._error = error

    def _get_relnotes_specs(self) -> Iterator[Dict[str, Any]]:
        """Read all YAML files that are found and return the relnotes.

        .. note::
            Each YAML file is expected to contain a list of one or more release
            note specs.

        .. note::
            Execute the error callback if any issue is faced when reading the
            source directory or when parsing YAML files, and stop looping over
            files.

        :yields: relnote specs found in each file.
        """
        directory = self.directory

        try:
            for file in os.listdir(directory):
                if not file.lower().endswith((".yml", ".yaml")):
                    continue
                for spec in safe_load(open(os.path.join(directory, file))):
                    yield spec
        except FileNotFoundError:
            self._error(f"Source directory does not exist: `{directory}`.")
        except NotADirectoryError:
            self._error("Source directory is not a directory, but a file: "
                        f"`{directory}`.")
        except Exception as exc:
            self._error("An unknown exception occurred while reading the "
                        f"source directory: {str(exc)}.")

    def _gather_relnotes(self) -> Dict[str, List[RelNote]]:
        """Gather all release notes found in YAML files.

        .. note::
            Execute the error callback if any issue is faced when parsing specs
            from YAML files.

        :returns: a dictionary. The keys are the release note types, and the
            values are list of release notes of the given type.
        """
        relnote_mapping = {type_: []
                           for type_ in RelNoteType.__members__.values()}

        # parse and group the relnotes by type
        for relnote_spec in self._get_relnotes_specs():
            try:
                relnote = RelNote(**relnote_spec)
            except (RelNoteInvalidType, RelNoteNoTicket) as exc:
                self._error(f"Faced an issue while parsing `{relnote_spec}`: "
                            f"{str(exc)}.")
            if relnote:
                relnote_mapping[relnote.type].append(relnote)

        return relnote_mapping

    def update_release_notes(self) -> None:
        """Update the release notes file based on found YAML files.

        .. note::
            Exceptions faced when processing might cause this method to quit
            the script execution with a error message.
        """
        file = self.file
        version = self.version
        date = self.date

        temp_file = NamedTemporaryFile('w', encoding='UTF-8')
        tf = temp_file.file

        with open(file, 'r', encoding='UTF-8') as f:
            # Write all existing lines up to the first release notes line --
            # release notes of a version are expected to be inside level 2
            # headers in the release notes file
            backup_line = None

            for line in f:
                if line.startswith("##"):
                    backup_line = line
                    break

                tf.writelines([line])

            # Write the new version and date
            tf.writelines([f"## {version} ({date.strftime('%Y-%m-%d')})\n\n"])

            # Write relnotes of the new version classified by type, with a
            # header at the beginning of each type
            for relnotes in self._gather_relnotes().values():
                for i, relnote in enumerate(relnotes):
                    tf.writelines([relnote.to_markdown(i == 0)])

            if backup_line:
                # Write the first version line that had been found before
                tf.writelines([backup_line,])

                # Write all the remaining lines that already existed
                for line in f:
                    tf.writelines([line])

        # Copy the new file content from temporary file to the actual release
        # notes file. ``flush`` takes care of making the content available for
        # copying, and ``close`` to get rid of the temporary file.
        tf.flush()
        copyfile(temp_file.name, file)
        tf.close()
