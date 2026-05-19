import re
import textwrap
from pathlib import Path


HEADER_RE = re.compile(r"\A(?:#[^\n]*\n)+")
DEP_BLOCK_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>\S+)\s*\\\s*\n"
    r"(?P<hashes>(?:[ \t]+--hash=sha256:[a-f0-9]+\s*\\?\s*\n)+)"
    r"(?P<comments>(?:[ \t]+#[^\n]*\n?)*)",
    re.MULTILINE,
)
HASH_RE = re.compile(r"--hash=sha256:([a-f0-9]+)")


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

    targets = [
        f"requirements-ppc64le{infix}.txt",
        f"requirements-s390x{infix}.txt",
    ]
    actuals = [f"requirements{infix}.txt"]

    target_deps = parse_requirements(targets)
    actual_deps = parse_requirements(actuals)

    for t_data in target_deps.values():
        for name, target_info in t_data["deps"].items():
            if not _merge_into_actuals(name, target_info, actual_deps):
                _report_unmatched(name, target_info, actual_deps)

    _render_template(actual_deps)


def _merge_into_actuals(name, target_info, actual_deps):
    """Union the target hash set into every matching actual dependency.

    A match requires the same dependency name and the same version
    string. Returns True if at least one actual dep was matched.
    """
    matched = False
    for a_data in actual_deps.values():
        actual = a_data["deps"].get(name)
        if actual and actual["version"] == target_info["version"]:
            actual["hash_set"] |= target_info["hash_set"]
            matched = True
    return matched


def _report_unmatched(name, target_info, actual_deps):
    """Print a diagnostic for a target dep that couldn't be reconciled."""
    print(
        textwrap.dedent(
            f"""
            {name}:{target_info['version']}
            with hashes: {target_info['hash_set']}
            could not be matched in files {actual_deps.keys()}.
            """
        )
    )


def parse_requirements(files):
    """Parse pip-compile output into a dict keyed by filename.

    For each input file, the returned mapping contains the leading
    header comments and a per-dependency entry of the form
    ``{name, version, hash_set, comment}``. Hashes are collected into a
    set; the trailing ``# via ...`` lines are captured as a list of
    stripped comment strings.
    """
    dependencies = {}
    for file in files:
        text = Path(file).read_text()
        header_match = HEADER_RE.match(text)
        header = (
            header_match.group(0).splitlines(keepends=True) if header_match else []
        )
        deps = {
            m["name"]: {
                "name": m["name"],
                "version": m["version"],
                "hash_set": set(HASH_RE.findall(m["hashes"])),
                "comment": [
                    line.strip() for line in m["comments"].splitlines() if line.strip()
                ],
            }
            for m in DEP_BLOCK_RE.finditer(text)
        }
        dependencies[file] = {"comment_header": header, "deps": deps}
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
