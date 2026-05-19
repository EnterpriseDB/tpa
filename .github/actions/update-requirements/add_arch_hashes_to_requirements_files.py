import sys
import textwrap
from pathlib import Path


def main():
    for infix in ["", "-rh8"]:
        add_hashes(infix)
    exit()


def add_hashes(infix):
    """
    Verify that all target requirements entries can be match (version and hash)
    inside the actual requirement files that should be updated right before the
    script is run.

    Will try to reconcile the actual requirement file by adding the missing
    hash in the correct dependency entry hash list when the version is
    matching.

    Otherwise will output in stdout the failed dependency and the missing hash
    in order to log the failure.

    Args:
        actuals (list[str]): list of filename to check target deps against.

    """

    # List of files holding dependencies we want to ensure are still being used.
    TARGETS = [
        f"requirements-ppc64le{infix}.txt",
        f"requirements-s390x{infix}.txt",
    ]

    actuals = [
        f"requirements{infix}.txt",
    ]

    # parse the files and generate both target and actual deps dicts
    target_deps = parse_requirements(TARGETS)
    actual_deps = parse_requirements(actuals)

    # walk through target deps entries (version and hash_set)
    for t_file in target_deps.keys():
        for t_dep in target_deps[t_file]["deps"].keys():
            ret = False
            # walk through actual deps entries
            for a_file in actual_deps.keys():
                for a_dep in actual_deps[a_file]["deps"].keys():

                    # comparing set of hashes, verify that target is a subset of actual dep's hash list
                    # otherwise we compare target version strings and add the hash to the list if version matches.
                    if t_dep == a_dep and (
                        actual_deps[a_file]["deps"][a_dep]["version"]
                        == target_deps[t_file]["deps"][t_dep]["version"]
                    ):
                        # ensure the hash is present in the actual file hash_set
                        actual_deps[a_file]["deps"][a_dep]["hash_set"] = actual_deps[
                            a_file
                        ]["deps"][a_dep]["hash_set"].union(
                            target_deps[t_file]["deps"][t_dep]["hash_set"]
                        )
                        ret = True

            # if we reach this and ret is still False the dep is not in the actual files
            # we need to output the failed dependency name and hash.
            if not ret:
                print(
                    textwrap.dedent(
                        f"""
                                    {t_dep}:{target_deps[t_file]["deps"][t_dep]['version']}
                                    with hashes: {target_deps[t_file]["deps"][t_dep]['hash_set']}
                                    could not be matched in files {actual_deps.keys()}.
                                    """
                    )
                )
    _render_template(actual_deps)


def parse_requirements(files: list):
    """Takes a list of filename and generate a dict of dependencies
    as follow:
    {
    filename: {
        'comment_header': ['#comment line 1', 'comment line 2'],
        'deps': {
            dep_name: {
                'version': 'a.b.c'
                'hash_set': {'hash_value_a','hash_value_b'}
                'comment': ['# via requirements.in']
            },
            ...
        },
    },
    filename: {
        'comment_header': ['#comment line 1', 'comment line 2'],
        'deps': {
            dep_name: {
                'version': 'a.b.c'
                'hash_set': {'hash_value_a','hash_value_b'}
                'comment': ['# via requirements.in']
            },
            ...
        },
    },
    ...
    }

    Args:
        files (list[str]): list of filenames to read and extract deps from.

    Returns:
        dict: returns a dict of all the dep with their version and hash_set per file.
    """
    dependencies = {}
    for file in files:
        file_dependencies = {file: {"header_comment": [], "deps": {}}}
        with open(file) as f:
            hash_set = set()
            comment = []
            header = []
            for entry in f:
                # first lines of the file are header comments
                if (
                    file_dependencies[file]["deps"] == {}
                    and not hash_set
                    and entry.startswith("#")
                ):
                    header.append(entry)
                # starting line of a dependency dep==a.b.c \
                elif "==" in entry:
                    # if we already added something in hash_set
                    # it means we have a dep ready to be added to the dict
                    if hash_set:
                        _add_dep(
                            file, name, version, hash_set, comment, file_dependencies
                        )

                    # save the new dependency name and version
                    name, version = entry.split()[0].split("==")
                    # reset the hash_set
                    hash_set = set()
                    comment = []
                # new hash entry
                # --hash=sha256:asdlkfjasdlfjkasdl \
                # or --hash=sha256:asdlkfjasdlfjkasdl
                elif entry.strip().startswith("--"):
                    hash_set.add(entry.strip().strip("\\").split(":")[1].strip())
                elif entry.strip().startswith("#") and hash_set:
                    comment.append(entry.strip().strip("\n"))

            # once the loop over the file ends, we still have the last dep to add
            _add_dep(file, name, version, hash_set, comment, file_dependencies)
            _add_header(file, header, file_dependencies)
        # add the entire file_dependencies to the main dict
        dependencies.update(file_dependencies)
    return dependencies


def _add_header(file, header, file_dependencies):
    file_dependencies[file]["comment_header"] = header


def _add_dep(file, name, version, hash_set, comment, file_dependencies):

    _dep = {
        name: {
            "name": name,
            "version": version,
            "hash_set": hash_set,
            "comment": comment,
        }
    }
    file_dependencies[file]["deps"].update(_dep)


def _render_template(actual_deps):
    """Write each requirements file with its dependency entries rebuilt
    from parsed data.

    Hashes are emitted alphabetically for deterministic output. Layout
    mirrors what pip-compile produces (four-space indent for hash and
    `via` comment lines).
    """
    for a_file, file_data in actual_deps.items():
        chunks = ["".join(file_data["comment_header"]).strip()]
        for dep in file_data["deps"].values():
            hashes = " \\\n    --hash=sha256:".join(sorted(dep["hash_set"]))
            comment = "\n    ".join(dep["comment"])
            chunks.append(
                f"{dep['name']}=={dep['version']} \\\n"
                f"    --hash=sha256:{hashes}\n"
                f"    {comment}"
            )
        Path(a_file).write_text("\n".join(chunks))


if __name__ == "__main__":  # pragma: no cover
    main()
