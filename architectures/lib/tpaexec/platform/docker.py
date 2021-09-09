#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

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
        errors = []
        sources = args.get("local_source_directories") or []
        installable = self.arch.installable_sources()
        local_sources = {}

        # We accept a list of "name:/host/dir/[:/container/dir[:flags]]"
        # arguments here, and transform it into a list of docker volume
        # definitions. The name must correspond to a product that
        # --install-from-source recognises.

        for s in sources:
            if ":" not in s:
                errors.append("expected name:/path/to/source, got %s" % s)
                continue

            (name, vol) = s.split(":", 1)

            if name.lower() not in installable.keys():
                errors.append("doesn't know what to do with sources for '%s'" % name)
                continue

            parts = vol.split(":", 2)

            host_path = os.path.abspath(os.path.expanduser(parts[0]))
            if not os.path.isdir(host_path):
                errors.append(
                    "can't find source directory for '%s': %s" % (name, host_path)
                )
                continue

            dirname = name
            if "name" in installable[name]:
                dirname = installable[name]["name"]

            container_path = "/opt/postgres/src/%s" % dirname
            if len(parts) > 1:
                container_path = parts[1]

            flags = "ro"
            if len(parts) > 2:
                container_path = parts[2]

            local_sources[name] = "%s:%s:%s" % (host_path, container_path, flags)

        if errors:
            for e in errors:
                print("ERROR: --local-source-directories %s" % (e), file=sys.stderr)
            sys.exit(-1)

        # If we're going to be building anything from source, we set up a shared
        # ccache. By default, this is a named Docker volume shared between the
        # containers in the cluster, so that it doesn't affect anything on the
        # host. Specify --shared-ccache to use a host directory instead.

        if args.get("install_from_source"):
            ccache = args.get("shared_ccache")
            if ccache:
                ccache = os.path.abspath(os.path.expanduser(args.get("shared_ccache")))
                if not os.path.isdir(ccache):
                    try:
                        os.mkdir(ccache)
                    except Exception as e:
                        print("ERROR: --shared-ccache: %s" % str(e), file=sys.stderr)
                        sys.exit(-1)
            else:
                # We don't have access to the cluster name here (it's set only
                # in process_arguments), so we leave a '%s' to be filled in by
                # update_instance_defaults() below.
                ccache = "ccache-%%s-%s" % time.strftime(
                    "%Y%m%d%H%M%S", time.localtime()
                )

            self.ccache = "%s:/root/.ccache:rw" % ccache

        args["local_sources"] = local_sources

    def supported_distributions(self):
        return [
            "Debian",
            "RedHat",
            "Ubuntu",
        ]

    def default_distribution(self):
        return "RedHat"

    def image(self, label, **kwargs):
        image = {}

        if label in self.supported_distributions():
            label = "tpa/%s" % label.lower()
            version = kwargs.get("version")
            if version and version != "latest":
                known_versions = {
                    "tpa/debian": ["9", "10", "11", "stretch", "buster", "bullseye"],
                    "tpa/ubuntu": ["18.04", "20.04", "bionic", "focal"],
                    "tpa/redhat": ["7", "8"],
                }

                if version not in known_versions[label]:
                    print(
                        "ERROR: %s:%s is not supported" % (label, version),
                        file=sys.stderr,
                    )
                    sys.exit(-1)

                label = label + ":" + version

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
                    pass
                else:
                    newvolumes.append(v)
            if volumes:
                i["volumes"] = newvolumes

    def process_arguments(self, args):
        s = args.get("platform_settings") or {}

        docker_images = args.get("docker_images")
        if docker_images:
            s["docker_images"] = docker_images

        args["platform_settings"] = s
