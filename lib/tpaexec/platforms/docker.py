#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from . import Platform

import os
import time

from ..exceptions import DockerPlatformError


class docker(Platform):
    def __init__(self, name, arch):
        super().__init__(name, arch)
        self.ccache = None

    def add_platform_options(self, p, g):
        g.add_argument("--shared-ccache", metavar="PATH")
        g.add_argument("--local-source-directories", nargs="+", metavar="NAME:PATH")

    def validate_arguments(self, args):
        local_sources, errors = self._validate_sources(
            args.get("local_source_directories") or []
        )
        if errors:
            raise DockerPlatformError(
                *(f"--local-source-directories {e}" for e in errors)
            )

        if args.get("enable_local_repo"):
            local_sources["local-repo"] = ":".join(
                [
                    os.path.abspath(os.path.join(self.arch.cluster, "local-repo")),
                    "/var/opt/tpa/local-repo",
                    "ro",
                ]
            )

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
                    raise DockerPlatformError(f"--shared-ccache: {str(e)}")
        else:
            # We don't have access to the cluster name here (it's set only
            # in process_arguments), so we leave a '%s' to be filled in by
            # update_instance_defaults() below.
            ccache = "ccache-%%s-%s" % time.strftime("%Y%m%d%H%M%S", time.localtime())
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
                errors.append(f"can't find source directory for '{name}': {host_path}")
                continue

            dirname = name
            if "name" in installable[name]:
                dirname = installable[name]["name"]
            flags = "ro"

            container_path = f"/opt/postgres/src/{dirname}"
            if len(parts) > 1:
                container_path = parts[1]

            if len(parts) > 2:
                container_path = parts[2]

            local_sources[name] = f"{host_path}:{container_path}:{flags}"

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

        Returns: dictionary with key "name", also keys "version" and "os" if known,
        and key "preferred_python_version" if the image has a preference

        """
        image = {}
        name, _, version = label.partition(":")
        _, _, img = name.rpartition("/")

        known_images = {
            "tpa/debian": {
                "versions": ["stretch", "buster", "bullseye", "9", "10", "11"],
                "os": "Debian",
            },
            "tpa/ubuntu": {
                "versions": ["bionic", "focal", "18.04", "20.04"],
                "os": "Ubuntu",
            },
            "tpa/redhat": {
                "versions": ["7", "8"],
                "os": "RedHat",
            },
            "tpa/rocky": {
                "versions": ["8"],
                "os": "Rocky",
                "os_family": "RedHat",
            },
            "tpa/almalinux": {
                "versions": ["8"],
                "os": "AlmaLinux",
                "os_family": "RedHat",
            },
        }

        def valid_version(img_name, ver):
            ver = ver or kwargs.get("version")
            if (
                ver
                and ver != "latest"
                and ver not in known_images[img_name]["versions"]
            ):
                raise DockerPlatformError(
                    f"ERROR: image {img_name}:{ver} is not supported"
                )
            return ver or known_images[img_name]["versions"].pop()

        # Cater for image names, e.g. "tpa/debian" or "tpa/debian:10"
        if name in known_images:
            image = known_images[name]
            image["version"] = valid_version(name, version)
            del image["versions"]
            image.setdefault("os_family", image.get("os"))

        # Cater for OS names, e.g. "Debian"
        if name in self.supported_distributions():
            image_name = f"tpa/{name.lower()}"
            image = known_images[image_name]
            version = valid_version(image_name, version)
            image["version"] = version
            label = image_name + ":" + version
            image.setdefault("os_family", image.get("os"))

        image["name"] = label
        if image["name"] == "tpa/redhat:7" or image["name"] == "centos/systemd":
            image["preferred_python_version"] = "python2"

        return image

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
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
