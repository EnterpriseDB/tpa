#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import ipaddress
import sys

from . import Platform


class vagrant(Platform):
    def add_platform_options(self, p, g):
        g.add_argument(
            "--provider",
            default="virtualbox",
            choices=["virtualbox"],
            help="virtualbox is currently the only supported provider",
        )
        g.add_argument("--memory", type=int, metavar="MB")
        g.add_argument(
            "--proxyconf",
            metavar="PROXY",
            help="[vagrant-proxyconf] proxy URL to configure on VMs",
        )
        g.add_argument(
            "--inject-ca-certificates",
            metavar="DIR",
            dest="capath",
            help="[vagrant-ca-certificates] CA certificates to configure on VMs",
        )

    def supported_distributions(self):
        return [
            "Debian",
            "RedHat",
            "Ubuntu",
        ]

    def default_distribution(self):
        return "Debian"

    def image(self, label, **kwargs):
        images = {
            "debian": {
                "8": "debian/jessie64",
                "jessie": "debian/jessie64",
                "9": "debian/stretch64",
                "stretch": "debian/stretch64",
                "10": "debian/buster64",
                "buster": "debian/buster64",
                "11": "debian/bullseye64",
                "bullseye": "debian/bullseye64",
                "default": "debian/bullseye64",
            },
            "redhat": {
                "7": "centos/7",
                "8": "centos/8",
                "default": "centos/8",
            },
            "ubuntu": {
                "16.04": "ubuntu/xenial64",
                "xenial": "ubuntu/xenial64",
                "18.04": "ubuntu/bionic64",
                "bionic": "ubuntu/bionic64",
                "default": "ubuntu/bionic64",
                "20.04": "ubuntu/focal64",
                "focal": "ubuntu/focal64",
            },
        }

        image = {}
        label = label.lower()
        version = kwargs.get("version") or "default"
        image["name"] = images.get(label, {"default": label}).get(version)

        if not image["name"]:
            print(
                "ERROR: cannot determine vagrant box name for %s/%s" % (label, version),
                file=sys.stderr,
            )
            print(
                "(Use ``--os-image box/name`` to specify one explicitly)",
                file=sys.stderr,
            )
            sys.exit(-1)

        image["user"] = "admin"
        return image

    def update_cluster_vars(self, cluster_vars, args, **kwargs):
        preferred_python_version = "python3"
        if args["image"]["name"] in ["debian/jessie64", "centos/7"]:
            preferred_python_version = "python2"
        cluster_vars["preferred_python_version"] = cluster_vars.get(
            "preferred_python_version", preferred_python_version
        )

    def update_instance_defaults(self, instance_defaults, args, **kwargs):
        if args["memory"]:
            instance_defaults.update({"memory": args["memory"]})
        instance_defaults.update({"image": args["image"]["name"]})

    def update_instances(self, instances, args, **kwargs):
        addresses = list(ipaddress.ip_network(args["subnets"][0]).hosts())

        for i, instance in enumerate(instances):
            instance["ip_address"] = str(addresses[i + 1])

    def process_arguments(self, args):
        s = {}

        if args["proxyconf"]:
            s["vagrant_proxyconf"] = args["proxyconf"]
        if args["capath"]:
            s["vagrant_ca_certificates"] = args["capath"]

        if s:
            args["platform_settings"] = s
