#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from . import Platform

import os, sys, time


class docker(Platform):
    def __init__(self, name, arch):
        super().__init__(name, arch)
        self.ccache = None

    def add_platform_options(self, p, g):
        g.add_argument("--shared-ccache", metavar="PATH")
        g.add_argument("--local-source-directories", nargs="+", metavar="NAME:PATH")

    def validate_arguments(self, args):
        local_sources, errors = self._validate_sources(args.get("local_source_directories") or [])
        if errors:
            for e in errors:
                print(f"ERROR: --local-source-directories {e}", file=sys.stderr)
            sys.exit(-1)
        args["local_sources"] = local_sources

        if args.get("install_from_source"):
            self._validate_ccache(args.get("shared_ccache"))

    def _validate_ccache(self, shared):
        """
        Setup shared ccache.

        If we're going to be building anything from source, we set up a shared
        ccache. By default, this is a named Docker volume shared between the
        containers in the cluster, so that it doesn't affect anything on the
        host.

        Args:
            shared: Specify a path to a shared ccache to use a host directory instead.

        """
        if shared:
            ccache = os.path.abspath(os.path.expanduser(shared))
            if not os.path.isdir(ccache):
                try:
                    os.mkdir(ccache)
                except OSError as e:
                    print(f"ERROR: --shared-ccache: {str(e)}", file=sys.stderr)
                    sys.exit(-1)
        else:
            # We don't have access to the cluster name here (it's set only
            # in process_arguments), so we leave a '%s' to be filled in by
            # update_instance_defaults() below.
            ccache = "ccache-%%s-%s" % time.strftime(
                "%Y%m%d%H%M%S", time.localtime()
            )
        self.ccache = f"{ccache}:/root/.ccache:rw"

    def _validate_sources(self, sources):
        """
        Validate the paths given for local source directories.

        Args:
            sources: We accept a list of "name:/host/dir/[:/container/dir[:flags]]" arguments here,
                     and transform it into a list of docker volume definitions.
                     The name must correspond to a product that --install-from-source recognises.

        """
        local_sources = {}
        installable = self.arch.installable_sources()
        errors = []
        for s in sources:
            if ":" not in s:
                errors.append(f"expected name:/path/to/source, got {s}")
                continue

            name, vol = s.split(":", 1)

            if name.lower() not in installable.keys():
                errors.append(f"doesn't know what to do with sources for '{name}'")
                continue

            parts = vol.split(":", 2)

            host_path = os.path.abspath(os.path.expanduser(parts[0]))
            if not os.path.isdir(host_path):
                errors.append(
                    f"can't find source directory for '{name}': {host_path}"
                )
                continue

            dirname = name
            if "name" in installable[name]:
                dirname = installable[name]["name"]

            container_path = f"/opt/postgres/src/{dirname}"
            if len(parts) > 1:
                container_path = parts[1]

            flags = "ro"
            if len(parts) > 2:
                container_path = parts[2]

            local_sources[name] = f"{host_path}:{container_path}:{flags}"

            self.ccache = "%s:/root/.ccache:rw" % ccache

        if args.get("enable_local_repo"):
            local_sources["local-repo"] = ":".join(
                [
                    os.path.abspath(os.path.join(self.arch.cluster, "local-repo")),
                    "/var/opt/tpa/local-repo",
                    "ro",
                ]
            )

        return local_sources, errors

    def supported_distributions(self):
        return ["Debian", "RedHat", "Ubuntu", "Rocky", "AlmaLinux"]

    def default_distribution(self):
        return "Rocky"

    def image(self, label, **kwargs):
        """
        Resolve an image name from known names.

        The label might match one of these formats:
        * the OS name, e.g. "Debian", converts to tpa image name, e.g. "tpa/debian".
        * a docker image, e.g. "tpa/debian"
        * a docker image with a version, e.g. "tpa/debian:11".

            image = {'name': 'tpa/debian', 'os': 'Debian', 'version': '11'}

        Args:
            label: The image label supplied as a default or on the command line
            **kwargs:

        Returns: dictionary with key "name", also keys "version" and "os" if known

        """
        image = {}
        name, _, version = label.partition(":")
        org, _, img = name.rpartition("/")

        known_versions = {
            "tpa/debian": ["stretch", "buster", "bullseye", "9", "10", "11"],
            "tpa/ubuntu": ["bionic", "focal", "18.04", "20.04"],
            "tpa/redhat": ["7", "8"],
            "tpa/rocky": ["8"],
            "tpa/almalinux": ["8"],
        }

        def valid_version(img_name, ver):
            ver = ver or kwargs.get("version")
            if ver and ver != "latest":
                if ver not in known_versions[img_name]:
                    print(
                        "ERROR: image %s:%s is not supported" % (img_name, ver),
                        file=sys.stderr,
                    )
                    sys.exit(-1)
            return ver or known_versions[image_name].pop()

        # Cater for image names, e.g. "tpa/debian" or "tpa/debian:10"
        if name in known_versions:
            image["os"] = img.capitalize()
            image_name = name
            image["version"] = valid_version(name, version)

        # Cater for OS names, e.g. "Debian"
        if name in self.supported_distributions():
            image["os"] = name
            image_name = "tpa/%s" % name.lower()
            version = valid_version(image_name, version)
            image["version"] = version
            label = image_name + ":" + version

        image["name"] = label

        return image

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        preferred_python_version = "python3"
        image = args["image"]
        if image:
            # Use tpa/redhat:7 by default for BDRv1 on RH, because we do not
            # publish packages for newer distributions. Specify `--os-version`
            # explicitly to override this decision.
            if (
                image["name"] == "tpa/redhat"
                and cluster_vars.get("postgresql_flavour") == "postgresql-bdr"
            ):
                image["name"] = "tpa/redhat:7"
            if image["name"] in ["centos/systemd", "tpa/redhat:7"]:
                preferred_python_version = "python2"
        cluster_vars["preferred_python_version"] = cluster_vars.get(
            "preferred_python_version", preferred_python_version
        )
        cluster_vars["use_volatile_subscriptions"] = True

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        y = self.arch.load_yaml("platforms/docker/instance_defaults.yml.j2", args)
        if y:
            if self.ccache:
                sources = y.get("local_source_directories", [])
                if "%s" in self.ccache:
                    sources.append(self.ccache % args["cluster_name"])
                else:
                    sources.append(self.ccache)
                y["local_source_directories"] = sources
            instance_defaults.update(y)

    def update_instances(self, instances, args, **kwargs):
        for i in instances:
            newvolumes = []
            volumes = i.get("volumes", [])
            for v in volumes:
                if "volume_type" in v and v["volume_type"] == "none":
                    continue
                else:
                    newvolumes.append(v)
            if volumes:
                i["volumes"] = newvolumes
                if not i["volumes"]:
                    del i["volumes"]

    def process_arguments(self, args):
        s = args.get("platform_settings") or {}

        docker_images = args.get("docker_images")
        if docker_images:
            s["docker_images"] = docker_images

        args["platform_settings"] = s
