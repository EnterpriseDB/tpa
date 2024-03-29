"""Helper module to update release notes."""
from argparse import ArgumentParser, Namespace
from datetime import date
import sys

from relnotes.base import RelNotesHandler


def fatal(msg: str) -> None:
    """Exit with a fatal error *msg*.

    :param msg: error message.
    """
    sys.exit(msg)


def parse_args() -> Namespace:
    """Parse command-line options.

    Require 3 arguments:

        * ``--source-directory``: path to a directory containing YAML files
            with the release notes specs;
        * ``--output-file``: path to a markdown file where parsed release notes
            will be written to. If the file already exists, the parsed notes
            are placed on top;
        * ``--version``: the version which notes we will fetch from the input
            file refer to.
        * ``--date``: the release date.

    :returns: :class:`~argparse.Namespace` generated by
        :func:`~argparse.ArgumentParser.parse_args`.
    """
    parser = ArgumentParser(description="Generate release notes for the "
                            "requested version")
    parser.add_argument("-s", "--source-directory", type=str, required=True,
                        help="Directory where the release note files to be "
                        "parsed in YAML format are")
    parser.add_argument("-o", "--output-file", type=str, required=True, help=""
                        "Output file in markdown format where release notes "
                        "information will be written to")
    parser.add_argument("-v", "--version", type=str, required=True, help=""
                        "Version that is being released")
    parser.add_argument("-d", "--date", type=date.fromisoformat, required=True,
                        help="Release date")
    return parser.parse_args()


def main() -> None:
    """Perform main logic of the script.

    Parse command-line arguments and parse each relnote spec found in the input
    file.
    """
    args = parse_args()
    handler = RelNotesHandler(args.source_directory, args.output_file,
                              args.version, args.date, fatal)
    handler.update_release_notes()


if __name__ == "__main__":
    main()
