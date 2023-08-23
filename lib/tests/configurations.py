#!/usr/bin/env python3
"""
This script generates a large number of valid `tpaexec configure` invocations
based on the option definitions below (and not on the actual ArgumentParser,
which would be ideal, but also more work than I want to do right now).

Here's an example of how I used it to test for configuration changes compared to
an earlier released version of TPA:

1. Generate list of configurations to test:

   python3 ./configurations.py > all-configurations

2. Generate a bunch of configurations using the devel branch:

   mkdir generated-by-devel
   cd generated-by-devel
   time bash -x ../all-configurations

3. Generate a bunch of configurations using the last released version:

   git checkout -b tmp v23.20
   mkdir generated-by-release
   cd generated-by-release
   time bash -x ../all-configurations

4. Generate a list of differences between the repository configurations of the
   corresponding clusters (which have the same numbers in both runs). Requires
   yq(1) from https://github.com/mikefarah/yq/ for convenience.

   mkdir repo-configs
   EXPR='{"edb_repositories": .cluster_vars.edb_repositories,
   "tpa_2q_repositories": .cluster_vars.tpa_2q_repositories,
   "apt_repository_list": .cluster_vars.apt_repository_list,
   "yum_repository_list": .cluster_vars.yum_repository_list}'

   for i in [0-9]*; do
       yq "$EXPR" < "$i"/config.yml > repo-configs/release-"$i"-repos.yml;
       if [[ -d ../generated-by-devel/"$i" ]]; then
           yq "$EXPR" < ../generated-by-devel/"$i"/config.yml > repo-configs/devel-"$i"-repos.yml;
       fi
       cmp repo-configs/release-"$i"-repos.yml repo-configs/devel-"$i"-repos.yml;
   done > differences 2>&1

5. Review the differences manually for any desired range of mismatches:

   # Note: $(seq -f "%02g" 0 10) ⇒ 00 01 02 … 10 (but does it work on MacOS X?)
   for i in $(seq 10 20); do
       if grep "$i-repos" differences >/dev/null; then
           grep "configure $i " ../all-configurations; echo;
           head repo-configs/release-"$i"-repos.yml repo-configs/devel-"$i"-repos.yml; echo;
       fi
   done | less

"""

import itertools
from typing import List, Union, Any

architectures = {
    "M1": {
        "required_options": {
            "--failover-manager": ["efm", "patroni", "repmgr"],
        },
    },
    "BDR-Always-ON": {
        "required_options": {
            "--harp-consensus-protocol": ["bdr"],  # Don't need ["etcd"],
            "--layout": ["bronze"],  # Don't need ["silver", "gold", "platinum"],
        },
    },
    "PGD-Always-ON": {
        "required_options": {
            "--pgd-proxy-routing": ["global"],  # Don't need ["local"],
        },
    },
}

# We don't expect to use different repositories on Debian and Ubuntu or between
# RedHat 7 and 8, for example, so we don't need to list all of the OSes that we
# support here.

oses = {
    "Debian": ["11"],
    "RedHat": ["8"],
}

# We don't expect to use different repositories for different versions of
# Postgres either, so we don't need to list all the possibilities here.

versions = ["14"]

flavours_and_versions = [["--postgresql", "--pgextended", "--edbpge"], versions]

epas_and_versions = [
    ["--epas"],
    versions,
    ["--redwood"], # Don't need ["--no-redwood"],
]

mixin_options = {
    "--enable-pem": [],
}


def flatten(choices: List[Any]) -> List[str]:
    result = []
    for elem in choices:
        if isinstance(elem, list):
            # Note that we skip empty lists in the input, such as would be
            # generated for mixin_options.
            for subelem in flatten(elem):
                result.append(subelem)
        else:
            result.append(elem)
    return result


def configurations():
    for arch in architectures:
        args = [["--architecture"], [arch]]
        for opt, vals in architectures[arch]["required_options"].items():
            args += [[opt], vals]

        # Convert the cross-product of ["--postgresql", …] × ["10", …, "15"]
        # into a list of possible choices, like [["--postgresql", "10"], …].
        flavour_choices = list(map(list, itertools.product(*flavours_and_versions)))
        flavour_choices += list(map(list, itertools.product(*epas_and_versions)))

        # We handle OS/version combinations the same way, except that each OS
        # has different versions.
        os_choices = []
        for os, vers in oses.items():
            os_choices += list(
                map(
                    list,
                    itertools.product(
                        [["--os", os]], list(map(lambda v: ["--os-version", v], vers))
                    ),
                )
            )

        # Mixin options may or may not occur at all, and may or may not have
        # more arguments when they do.
        mixin_choices = []
        for opt, vals in mixin_options.items():
            choices = [[opt]]
            if vals:
                choices += [vals]

            none_or_any = [[]] + list(map(list, itertools.product(*choices)))
            mixin_choices += none_or_any

        # We compute the cross product of a list where each element is a list
        # with either one element (e.g., ["--architecture"], where exactly that
        # value must occur at that position) or multiple elements (e.g., ["bdr",
        # "etcd"], which expand to an equal number of output combinations. The
        # individual choices may be lists (e.g., [] or ["--postgresql", "10"],
        # which must be flattened in the output).
        permutations = itertools.product(
            *args, os_choices, flavour_choices, mixin_choices
        )
        for p in permutations:
            yield flatten(list(p))


if __name__ == "__main__":
    for n, cfg in enumerate(configurations()):
        print(" ".join(["tpaexec", "configure", f"{n:02}", "--no-git"] + cfg))
