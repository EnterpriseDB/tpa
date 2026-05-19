import textwrap
from pathlib import Path


def main():
    for infix in ["", "-rh8"]:
        add_hashes(infix)


def add_hashes(infix):
    """Merge per-architecture hashes into the main requirements file.

    Reads the ppc64le and s390x variants for the given infix ("" or
    "-rh8"), parses the main requirements file, and unions any missing
    hashes whose dependency name and version match. Writes the merged
    result back via _render_template. If a target dependency cannot be
    matched in the actuals (missing entry or version mismatch), prints
    a diagnostic to stdout so the caller can fail the workflow step.
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


def parse_requirements(files):
    """Parse pip-compile output into a dict keyed by filename.

    For each input file, the returned mapping contains the leading
    header comments and a per-dependency entry of the form
    ``{name, version, hash_set, comment}``. Hashes are collected into a
    set; the trailing ``# via ...`` lines are captured as a list of
    comment strings.
    """
    dependencies = {}
    for file in files:
        file_data = {"comment_header": [], "deps": {}}
        with open(file) as f:
            header = []
            comment = []
            hash_set = set()
            name = version = None
            for entry in f:
                if file_data["deps"] == {} and not hash_set and entry.startswith("#"):
                    header.append(entry)
                elif "==" in entry:
                    if hash_set:
                        file_data["deps"][name] = {
                            "name": name,
                            "version": version,
                            "hash_set": hash_set,
                            "comment": comment,
                        }
                    name, version = entry.split()[0].split("==")
                    hash_set = set()
                    comment = []
                elif entry.strip().startswith("--"):
                    hash_set.add(entry.strip().strip("\\").split(":")[1].strip())
                elif entry.strip().startswith("#") and hash_set:
                    comment.append(entry.strip().strip("\n"))

            file_data["deps"][name] = {
                "name": name,
                "version": version,
                "hash_set": hash_set,
                "comment": comment,
            }
            file_data["comment_header"] = header
        dependencies[file] = file_data
    return dependencies


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
