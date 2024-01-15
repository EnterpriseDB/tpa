#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.
import sys
import os
import io
import uuid
import subprocess
import argparse
import shutil
from pathlib import Path

import yaml
import re

from typing import List

from ansible.template import Templar
from ansible.utils.vars import merge_hash
from functools import reduce

from .exceptions import ArchitectureError, ExternalCommandError
from .net import Network, DEFAULT_SUBNET_PREFIX_LENGTH, DEFAULT_NETWORK_CIDR
from .platforms import Platform

KEYRING_SUPPORTED_BACKENDS = ["system", "legacy"]


class Architecture(object):
    """
    This is the base class for TPA architectures, and it knows how to generate a
    configuration based on architecture-specific defaults defined by subclasses,
    as well as user input in the form of command-line options.
    """

    def __init__(self, directory, lib, argv=None):
        """
        We expect this constructor to be invoked via a subclass defined in
        architectures/Xyzzy/configure; self.name then becomes 'Xyzzy'. It
        creates a Platform object corresponding to any «--platform x» on the
        command-line.

        Args:
            directory: Path to directory containing architecture metadata, commands, templates, etc
            lib: Path to directory containing tpaexec commands, templates, etc
            argv: list of strings to be passed to the argument parser

        """
        self.dir = directory
        self.lib = lib
        self.name = os.path.basename(self.dir)
        self._argv = argv or []
        self.platform = Platform.load(self._argv, arch=self)
        self._args = None
        self._net = None

    ##
    ## Command-line parsing
    ##

    @property
    def args(self):
        if self._args is None:
            self._args = vars(self.argument_parser().parse_args(args=self._argv))
        return self._args

    @property
    def cluster(self):
        """
        The path to the cluster directory, as given to `tpaexec configure`, but
        with trailing slashes removed (to simplify path construction).
        """
        return re.sub("/*$", "", self.args["cluster"])

    def configure(self, force=False):
        """
        Obtains command-line arguments based on the selected architecture and
        platform, gives the architecture and platform a chance to process the
        configuration information, and generates a cluster configuration.
        """
        self.validate_arguments(self.args)
        self.process_arguments(self.args)
        configuration = self.generate_configuration()
        self.write_configuration(configuration, force=force)
        self.after_configuration(force=force)

    def argument_parser(self):
        """
        Returns an ArgumentParser object configured to accept the options
        relevant to the selected architecture and platform
        """
        prog = "tpaexec configure"
        p = argparse.ArgumentParser(
            prog=prog,
            usage="%s <cluster> --architecture %s [--help | …options…]"
            % (prog, self.name),
        )
        p.add_argument("cluster", help="path to cluster directory")
        self.add_options(p)
        self.set_defaults(p)
        return p

    def add_options(self, p):
        """
        Adds any relevant options to the parser object
        """
        p.add_argument(
            "-v",
            "--verbose",
            dest="verbosity",
            action="count",
            help="increase verbosity",
        )

        g = p.add_argument_group("architecture and platform selection")
        g.add_argument(
            "--architecture",
            "-a",
            required=True,
            choices=[self.name],
            help="currently selected architecture",
        )
        layouts = self.layout_names()
        if layouts:
            g.add_argument(
                "--layout",
                required=self.default_layout_name() is None,
                choices=self.layout_names(),
                default=self.default_layout_name(),
                help="architecture-specific layout selection",
            )
        g.add_argument(
            "--platform",
            default="aws",
            choices=self.supported_platforms(),
            help="platforms supported by %s (selected: %s)"
            % (self.name, self.platform.name),
        )

        # Options relevant to this architecture
        g = p.add_argument_group("%s architecture options" % self.name)
        self.add_architecture_options(p, g)

        # Options relevant to the selected platform
        g = p.add_argument_group("%s platform options" % self.platform.name)
        self.platform.add_platform_options(p, g)

        g = p.add_argument_group("cluster options")
        g.add_argument("--owner")
        g.add_argument("--overrides-from", nargs="+", metavar="FILE")
        g.add_argument(
            "--no-git",
            action="store_true",
            dest="no_git",
            help="don't create cluster dir as a local git repository",
        )

        g = p.add_argument_group("AAP/Tower options")
        g.add_argument(
            "--use-redhat-aac",
            "--use-ansible-tower",
            action="store",
            dest="tower_api_url",
            help="provision this cluster for use with Ansible Automation Controller (Tower)",
        )
        g.add_argument(
            "--tower-git-repository",
            action="store",
            dest="tower_git_repository",
            help="git remote repository to push Tower generated data",
        )

        g = p.add_argument_group("OS selection")
        labels = self.platform.supported_distributions()
        label_opts = {"choices": labels} if labels else {}
        default_label = self.platform.default_distribution()
        if default_label:
            label_opts["default"] = default_label
        elif labels and len(labels) == 1:
            label_opts["default"] = labels[0]
        g.add_argument(
            "--distribution", "--os", dest="distribution", metavar="LABEL", **label_opts
        )
        g.add_argument("--os-version", metavar="VERSION")
        g.add_argument("--os-image", metavar="LABEL")

        # When installing EPAS, you must specify whether to use Redwood mode
        # (with Oracle compatibility features enabled) or Postgres-compatible
        # mode. EPAS itself operates in Redwood mode by default (it's an initdb
        # option).
        g = p.add_argument_group("repository selection")

        g.add_argument(
            "--use-volatile-subscriptions",
            action="store_true",
        )
        g_repo = g.add_mutually_exclusive_group()
        g_repo.add_argument(
            "--2Q-repositories",
            dest="tpa_2q_repositories",
            nargs="+",
            metavar="source/name/maturity",
        )
        g_repo.add_argument(
            "--edb-repositories",
            dest="edb_repositories",
            nargs="+",
            metavar="repository",
        )

        g = p.add_argument_group("install from source options")
        g.add_argument("--install-from-source", nargs="+", metavar="NAME")
        for pkg in self.versionable_packages():
            g.add_argument("--%s-package-version" % pkg, metavar="VER")

        g = p.add_argument_group("software selection")
        g.add_argument(
            "--enable-pem",
            action="store_true",
            default=argparse.SUPPRESS,
            help="add a PEM monitoring server to the cluster",
        )
        g.add_argument(
            "--enable-pg-backup-api",
            action="store_true",
            default=argparse.SUPPRESS,
            help="install pg-backup-api on barman server and register to pem server if enabled",
        )
        g.add_argument("--extra-packages", nargs="+", metavar="NAME")
        g.add_argument("--extra-optional-packages", nargs="+", metavar="NAME")

        # A combination of --postgres-flavour and --postgres-version tells us
        # exactly which server to deploy. We need both things, but because we
        # support multiple ways to specify them, we don't mark the options as
        # required, just check that we have the value in validate_arguments.

        supported_flavours = ["postgresql", "pgextended", "edbpge", "epas"]
        supported_versions = ["10", "11", "12", "13", "14", "15", "16"]

        class FlavourAndMaybeVersionAction(argparse.Action):
            """Takes an option such as `--epas` or `--postgresql 15` and stores
            'epas' or ('postgresql', 15) to `dest`. This lets you avoid having
            to spell out `--postgres-flavour x --postgres-version y` all the
            time."""

            def __init__(self, option_strings, dest, nargs=None, **kwargs):
                # We have to validate `choices` ourselves, because with nargs=?,
                # if you say just --epas, argparse by default tries to validate
                # the `const` against `choices`.
                self.version_choices = kwargs.get("choices")
                kwargs = {k: v for k, v in kwargs.items() if k != "choices"}
                super().__init__(option_strings, dest, nargs=nargs, **kwargs)

            def __call__(self, parser, namespace, arg, option_string=None):
                value = None

                # `--epas` stores 'epas' (== `const`), `--edbpge 15` stores
                # ('edbpge', '15'), which validate_arguments will decode.
                if arg == self.const:
                    value = arg
                elif self.version_choices and arg not in self.version_choices:
                    raise ArchitectureError(
                        f"You must specify a version in [{', '.join(self.version_choices)}]"
                    )
                else:
                    value = (self.const, arg)

                setattr(namespace, self.dest, value)

        g = p.add_argument_group("postgres options")
        g_flavour = g.add_mutually_exclusive_group(required=True)
        g_flavour.add_argument(
            "--postgres-flavour",
            dest="postgres_flavour",
            choices=supported_flavours,
            help="select a Postgres flavour/distribution to install",
        )
        g_flavour.add_argument(
            "--postgresql",
            action=FlavourAndMaybeVersionAction,
            const="postgresql",
            nargs="?",
            dest="postgres_flavour",
            choices=supported_versions,
            help="install PostgreSQL",
            metavar="VERSION",
        )
        # There are two related variants of Postgres Extended.
        #
        # One is what we used to call 2ndQPostgres, which has the same package
        # names as Postgres, and is provided only through the legacy 2Q repos
        # for use with existing BDR 3 or 4 clusters (--pgextended). Its use
        # outside BDR-EE was never encouraged (though it used to work), and
        # that combination was explicitly removed from support.
        #
        # The other is EDB Postgres Extended, which has different package names
        # (edb-postgresextended*) and is available for use with new clusters
        # from the new repos, either by itself or with BDR 5 (--edbpge).
        #
        # Because these two flavours, which we MUST internally treat as distinct
        # (they have different default values and package names), cannot be used
        # in the same architecture, we are able to accept a single option and
        # translate it into different postgres_flavour settings based on the
        # context of its use.
        g_flavour.add_argument(
            "--edb-postgres-extended",
            "--pgextended",
            "--edbpge",
            action=FlavourAndMaybeVersionAction,
            const="edb-postgres-extended",
            nargs="?",
            dest="postgres_flavour",
            choices=supported_versions,
            help="install EDB Postgres Extended (formerly 2ndQuadrant Postgres)",
            metavar="VERSION",
        )
        g_flavour.add_argument(
            "--edb-postgres-advanced",
            "--epas",
            action=FlavourAndMaybeVersionAction,
            const="epas",
            nargs="?",
            dest="postgres_flavour",
            choices=supported_versions,
            help="install EDB Postgres Advanced Server (EPAS)",
            metavar="VERSION",
        )
        g.add_argument(
            "--postgres-version",
            dest="postgres_version",
            choices=supported_versions,
            help="select a major version of Postgres to install",
        )
        g.add_argument(
            "--extra-postgres-packages",
            nargs="+",
            metavar="NAME",
        )

        g = p.add_argument_group("EPAS options")
        g_redwood = g.add_mutually_exclusive_group()
        g_redwood.add_argument(
            "--redwood",
            action="store_true",
            dest="epas_redwood_compat",
            default=argparse.SUPPRESS,
            help="enable Oracle compatibility features for EPAS",
        )
        g_redwood.add_argument(
            "--no-redwood",
            "--no-redwood-compat",
            action="store_false",
            dest="epas_redwood_compat",
            default=argparse.SUPPRESS,
            help="disable Oracle compatibility features for EPAS",
        )

        g = p.add_argument_group("local repo")
        g_local = g.add_mutually_exclusive_group()
        g_local.add_argument(
            "--enable-local-repo",
            action="store_true",
            default=argparse.SUPPRESS,
            help="make packages available to instances from cluster_dir/local-repo",
        )
        g_local.add_argument(
            "--use-local-repo-only",
            action="store_true",
            help="make packages available to instances from cluster_dir/local-repo, and disable all other repositories",
            default=argparse.SUPPRESS,
        )

        g = p.add_argument_group("volume sizes in GB")
        for vol in ["root", "barman", "postgres"]:
            g.add_argument("--%s-volume-size" % vol, type=int, metavar="N")

        g = p.add_argument_group("network and subnet selection")
        g.add_argument("--network", metavar="NET")
        g.add_argument(
            "--exclude-subnets-from",
            metavar="DIR",
            action="append",
            dest="exclude_subnet_dirs",
            default=[],
        )
        g.add_argument("--no-shuffle-subnets", action="store_true")
        g.add_argument(
            "--subnet-prefix",
            default=DEFAULT_SUBNET_PREFIX_LENGTH,
            type=int,
            help="number of bits to use to define subnets, e.g. to create subnets as /26 use 26",
        )

        g = p.add_argument_group("hostname selection")
        g.add_argument("--hostnames-from", metavar="FILE")
        g.add_argument("--hostnames-pattern", metavar="PATTERN")
        g.add_argument("--hostnames-sorted-by", metavar="OPTION")
        g.add_argument("--hostnames-unsorted", action="store_true")
        g.add_argument("--cluster-prefixed-hostnames", action="store_true")

        g = p.add_argument_group("locations")
        g.add_argument("--location-names", metavar="LOCATION", nargs="+")

        g = p.add_argument_group("password management")
        g.add_argument(
            "--keyring-backend",
            help="backend used to store cluster's vault password",
            choices=KEYRING_SUPPORTED_BACKENDS,
            default=argparse.SUPPRESS,
        )

    def add_architecture_options(self, p, g):
        """
        Adds architecture-specific options to the (relevant group in the) parser
        (subclasses are expected to override this).
        """
        pass

    def set_defaults(self, p):
        """
        Set default values for command-line options
        """
        argument_defaults = self._argument_defaults()
        self.update_argument_defaults(argument_defaults)
        p.set_defaults(**argument_defaults)

    def _argument_defaults(self):
        """
        Returns a dict of defaults for the corresponding options
        """
        return {
            "root_volume_size": 16,
            "barman_volume_size": 32,
            "postgres_volume_size": 16,
        }

    def update_argument_defaults(self, argument_defaults):
        """
        Makes architecture-specific changes to argument_defaults if required
        """
        pass

    def default_platform(self):
        """
        Returns the default platform for this architecture (i.e., the platform
        that will be used if no «--platform x» is specified)
        """
        return "aws"

    def supported_platforms(self):
        """
        Returns a list of platforms supported by this architecture
        """
        return Platform.all_platforms()

    def default_location_names(self):
        """
        Returns a list of names for the locations used by the cluster
        """
        return ["first", "second", "third", "fourth"]

    ##
    ## Cluster configuration
    ##

    def validate_arguments(self, args):
        """
        Look at the arguments collected from the command-line and complain if
        anything seems wrong.
        """

        # By now, both postgres_flavour and postgres_version must be set,
        # whether they were specified separately or through a shortcut like
        # `--postgresql 14`.
        self._validate_flavour_version(args)

        # Validate arguments to --2Q-repositories
        self._validate_2q_repositories(args)

        # Validate arguments to --install-from-source
        self._validate_from_source(args)

        # --use-local-repo-only implies --enable-local-repo
        if self.args.get("use_local_repo_only"):
            self.args["enable_local_repo"] = True

        # use either command line or environment variable
        # to determine keyring backend, default to system.
        if not self.args.get("keyring_backend"):
            self.args["keyring_backend"] = os.environ.get(
                "TPA_KEYRING_BACKEND", "system"
            )

        self.platform.validate_arguments(args)

    def _validate_flavour_version(self, args):
        """Verify postgres flavour, version and related arguments.
        By now, both postgres_flavour and postgres_version must be set,
        whether they were specified separately or through a shortcut like
        `--postgresql 14`.
        """
        flavour = args.get("postgres_flavour")
        version = args.get("postgres_version")

        if isinstance(flavour, tuple):
            (flavour, v) = flavour
            if version and version != v:
                # We don't need to worry about conflicts between
                # `--postgres-flavour epas` and `--epas`, because they're in a
                # mutually exclusive group.
                raise ArchitectureError(
                    f"You must select a single Postgres version, '--{flavour} {v}' conflicts with '--postgres-version {version}'"
                )
            args["postgres_flavour"] = flavour
            args["postgres_version"] = version = v

        if not flavour:
            raise ArchitectureError(
                "You must select a Postgres flavour, e.g., with --postgresql or --edb-postgres-{extended,advanced}"
            )
        if not version:
            raise ArchitectureError(
                "You must select a Postgres version, e.g., with '--postgres-version 14'"
            )

        redwood = args.get("epas_redwood_compat")
        if flavour == "epas":
            if redwood is None:
                raise ArchitectureError(
                    "You must specify --redwood or --no-redwood to enable or disable Oracle compatibility features in EPAS"
                )
        elif redwood is not None:
            raise ArchitectureError(
                "You can specify --redwood/--no-redwood only when using EPAS"
            )

        # If you specify --edb-postgres-extended, we have to translate the value
        # to pgextended or edbpge depending on architecture.
        if flavour == "edb-postgres-extended":
            if self.name == "BDR-Always-ON":
                args["postgres_flavour"] = "pgextended"
            else:
                args["postgres_flavour"] = "edbpge"

        # The pgextended flavour implies the 2q repos and is therefore incompatible with PEM
        if args.get("postgres_flavour") == "pgextended" and args.get("enable_pem"):
            raise ArchitectureError(
                "PEM is not compatible with the BDR-Always-ON architecture and EDB Postgres Extended"
            )

    def _validate_2q_repositories(self, args):
        """Validate arguments to --2Q-repositories"""
        repos = args.get("tpa_2q_repositories") or []
        for r in repos:
            errors = []
            parts = r.split("/")
            if len(parts) == 3:
                errors = self._2q_repo_exists(parts, errors)
            else:
                errors.append("invalid name (expected source/product/maturity)")

            if errors:
                raise ArchitectureError(*(f"repository '{r}' has {e}" for e in errors))

    def _2q_repo_exists(self, parts, errors):
        """Ensure each part of a 2q repo is a valid input"""
        (source, name, maturity) = parts
        if source not in ["ci-spool", "products", "dl"]:
            errors.append(
                "unknown source '%s' (try 'dl', 'products', or 'ci-spool')" % source
            )
        if name not in self.product_repositories():
            errors.append("unknown product name '%s'" % name)
        if maturity not in ["snapshot", "testing", "release"]:
            errors.append(
                "unknown maturity '%s' (try 'release', 'testing', or 'snapshot')"
                % maturity
            )
        return errors

    def _validate_from_source(self, args):
        """Validate arguments to --install-from-source"""

        errors = []
        source_names = []
        sources = args.get("install_from_source") or []
        installable = self.installable_sources().keys()
        for name in sources:
            # We accept either something like 2ndqpostgres or
            # 2ndqpostgres:2QREL_11_STABLE_dev
            if ":" in name:
                (name, _) = name.split(":", 1)
            if name.lower() not in installable:
                errors.append("doesn't know how to install '%s' from source" % name)
            source_names.append(name.lower())
        if "postgres" in source_names and "2ndqpostgres" in source_names:
            errors.append("cannot install both Postgres and 2ndQPostgres")
        if "bdr3" in source_names and "pglogical3" not in source_names:
            errors.append("cannot build bdr3 without pglogical3")
        try:
            if source_names.index("pglogical3") > source_names.index("bdr3"):
                errors.append("should build pglogical3 before bdr3")
        except ValueError:
            pass

        if errors:
            raise ArchitectureError(*(f"--install-from-source {e}" for e in errors))

    def process_arguments(self, args):
        """
        Augment arguments from the command-line with enough additional
        information (based on the selected architecture and platform) to
        generate config.yml
        """

        # At this point, args is what the command-line parser gave us, i.e., a
        # combination of values specified on the command-line and defaults set
        # by the architecture. Now we start augmenting that information.

        args["cluster_name"] = self.cluster_name()

        # If --overrides-from is specified, we load files one by one (treating
        # them as templates) and merge them recursively into args. This can be
        # used to set cluster_tags, add stuff to instance_vars etc. We don't do
        # anything to restrict which keys this can be applied to, so it's quite
        # possible to misuse this to do things that don't make sense.
        overrides = args.get("overrides_from") or []
        for f in overrides:
            extra_vars = self.load_yaml(f, args, loader=self.loader([os.getcwd()]))
            args.update(reduce(merge_hash, [args, extra_vars]))

        # The architecture's num_instances() method should work by this point,
        # so that we can generate the correct number of hostnames.
        (args["hostnames"], args["ip_addresses"]) = self.hostnames(self.num_instances())
        if args.get("cluster_prefixed_hostnames"):
            args["hostnames"] = [
                re.sub("[^a-z0-9-]", "-", args["cluster_name"].lower()) + "-" + hostname
                for hostname in args["hostnames"]
            ]

        # Figure out how to get the desired distribution.
        args["image"] = self.image()

        # Set per platform volume device name prefix
        args["volume_device_name"] = self.platform.default_volume_device_name

        # Figure out the basic structure of the cluster.
        self.load_topology(args)

        if "instances" in args:
            for instance in args["instances"]:
                if args["ip_addresses"][instance["node"]] is not None:
                    instance["ip_address"] = args["ip_addresses"][instance["node"]]

        # Now that main.yml.j2 has been loaded, and we have the initial set of
        # instances[] defined, num_locations() should work, and we can generate
        # the necessary number of subnets.
        args["subnets"] = self.subnets(self.num_locations())

        locations = args.get("locations", [])
        if not locations:
            self._init_locations(locations)
        self.update_locations(locations)
        self.platform.update_locations(locations, args)
        args["locations"] = locations

        cluster_tags = args.get("cluster_tags", {})
        self.update_cluster_tags(cluster_tags)
        self.platform.update_cluster_tags(cluster_tags, args)
        args["cluster_tags"] = cluster_tags

        self._init_top_level_settings()

        cluster_vars = args.get("cluster_vars", {})
        self._init_cluster_vars(cluster_vars)
        self.update_cluster_vars(cluster_vars)
        self.postgres_eol_repos(cluster_vars)
        self.update_repos(cluster_vars)
        self.platform.update_cluster_vars(cluster_vars, args)
        args["cluster_vars"] = cluster_vars

        instance_defaults = args.get("instance_defaults", {})
        self._init_instance_defaults(instance_defaults)
        self.update_instance_defaults(instance_defaults)
        self.platform.update_instance_defaults(instance_defaults, args)
        args["instance_defaults"] = instance_defaults

        instances = args.get("instances", {})
        self._init_instances(instances)
        self.update_instances(instances)
        self.platform.update_instances(instances, args)
        args["instances"] = instances

        self.platform.process_arguments(args)

    def cluster_name(self):
        """
        Returns a name for the cluster
        """
        return os.path.basename(self.cluster)

    def num_instances(self):
        """
        Returns the number of instances required (which may be known beforehand,
        or based on a --num-instances option, etc.)
        """
        return self.args["num_instances"]

    def num_locations(self):
        """
        Returns the number of locations required by this architecture
        """
        locations = {}
        for i in self.args["instances"]:
            loc = i.get("location")
            if loc is not None:
                locations[loc] = 1
        return len(locations)

    def hostnames(self, num):
        """
        Returns two arrays. The first contains 'zero' followed by the
        requested number of hostnames, so that templates can assign
        hostnames[i] to node[i] without regard to the fact that we number
        nodes starting from 1.  The second contains the corresponding
        address for each hostname, or None if no address was provided.
        """

        env = {}
        for arg in [
            "hostnames_from",
            "hostnames_pattern",
            "hostnames_sorted_by",
            "hostnames_unsorted",
        ]:
            if self.args[arg] is not None:
                env[arg.upper()] = str(self.args[arg])

        popen_params = {}

        if int(str(sys.version_info.major) + str(sys.version_info.minor)) >= 36:
            popen_params["encoding"] = sys.getdefaultencoding()

        p = subprocess.Popen(
            ["%s/hostnames" % self.lib, str(num)],
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **popen_params,
        )
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            raise ArchitectureError(stderr.strip())

        names = []
        addresses = []
        for line in stdout.splitlines():
            fields = line.split()
            names.append(fields[0])
            addresses.append(fields[1] if len(fields) > 1 else None)
        return ["zero"] + names, [None] + addresses

    def image(self):
        """
        Returns the selected platform's choice of image for this cluster, based
        on the user's preferences.
        """
        label = self.args.get("os_image") or self.args["distribution"]
        version = self.args.get("os_version")
        return self.platform.image(label, version=version)

    def load_topology(self, args):
        """
        Returns the parsed contents of the template which defines the overall
        topology of the cluster. (It must be written so that we can expand it
        based on the correct number of hostnames and information from the
        command-line).
        """
        y = self.load_yaml(self.layout_template(args), args)
        if y is not None:
            args.update(y)

    def layout_template(self, args):
        """
        Returns the path to a template that defines the topology of the cluster,
        main.yml.j2 by default, or whatever --layout the user selected, if the
        architecture supports it.
        """
        layout = args.get("layout")
        if layout:
            layout = f"layouts/{layout}.yml.j2"
        return layout or "main.yml.j2"

    @property
    def net(self):
        """Return the top level network CIDR object."""
        if self._net is None:
            if self.args.get("network"):
                cidr = self.args["network"]
            else:
                cidr = self.args.get("subnet", DEFAULT_NETWORK_CIDR)

            self.args.setdefault("subnet_prefix", DEFAULT_SUBNET_PREFIX_LENGTH)
            net = Network(cidr, self.args["subnet_prefix"])
            self._net = net
        return self._net

    def subnets(self, num):
        """
        Returns the requested number of subnets.

        Perform exclusion checks on provided cluster directories and capacity checks against required location
        requirements.

        """
        subnets = self.net.subnets(limit=num)
        subnets.exclude(
            excludes=self._get_subnets_from(
                exclude_dirs=self.args.get("exclude_subnet_dirs", [])
            )
        )

        if len(list(subnets)) < num:
            raise ArchitectureError(
                f"Network {subnets.cidr.with_prefixlen} cannot contain {num} /{subnets.new_prefix} subnets. "
                f"You might want to try providing a larger network with --network or smaller subnets with"
                f" --subnet-prefix {subnets.new_prefix + 1}",
            )

        # This dramatically reduces conflicts between people who are deploying their clusters into the same VPC
        # otherwise we pick the same subnets in the network range every time
        if not self.args.get("no_shuffle_subnets"):
            subnets.shuffle()

        # Select a number of subnets according to the limit set (and convert from an iterator to a list of strings)
        return [str(s) for s in subnets]

    @staticmethod
    def _get_subnets_from(exclude_dirs):
        """
        Look for subnet ranges defined in the cluster config directory list provided.

        If any subnet exclusion directories are specified, look for "subnet: a.b.c.d/n" declarations in
        config.yml files within the given directories and exclude those subnets from the list.

        Args:
            exclude_dirs: List of directories to look in

        Returns: List of subnet ranges found

        """
        values = []
        for dir_name in exclude_dirs:
            try:
                with open(f"{dir_name}/config.yml") as exclude_config_yml:
                    config_data = yaml.safe_load(exclude_config_yml)
                    for key in ("instances", "locations"):
                        values.extend(
                            s["subnet"] for s in config_data.get(key) if s.get("subnet")
                        )
                    instance_default_subnet = config_data.get(
                        "instance_defaults", {}
                    ).get("subnet")
                    if instance_default_subnet:
                        values.append(instance_default_subnet)
            except FileNotFoundError:
                raise ArchitectureError(
                    f"Could not open a config.yml file in the provided path: {dir_name}"
                )
        return list(set(values))

    def _init_locations(self, locations):
        """
        Makes changes to locations applicable across architectures
        """
        names = self.args.get("location_names") or self.default_location_names()
        for li in range(0, self.num_locations()):
            locations.append({"Name": names[li]})

    def update_locations(self, locations):
        """
        Makes architecture-specific changes to locations if required
        """
        pass

    def update_cluster_tags(self, cluster_tags):
        """
        Makes architecture-specific changes to cluster_tags if required
        """
        pass

    def _init_top_level_settings(self):
        """Add top level settings applicable accross all architectures"""
        self._add_tower_settings()

        self._add_keyring_settings()

    def _add_tower_settings(self):
        """Add top level settings for Tower"""
        if self.args.get("tower_api_url"):
            top = self.args.get("top_level_settings") or {}
            top.update({"use_ssh_agent": "true"})

            tower = self.args.get("tower_settings") or {}
            tower.update({"api_url": self.args["tower_api_url"]})

            self.args["tower_settings"] = tower
            self.args["top_level_settings"] = top

        if self.args.get("tower_git_repository"):
            tower = self.args.get("tower_settings") or {}
            tower.update({"git_repository": self.args["tower_git_repository"]})
            self.args["tower_settings"] = tower

    def _add_keyring_settings(self):
        if self.args.get("keyring_backend"):
            top = self.args.get("top_level_settings") or {}
            top.update({"keyring_backend": self.args.get("keyring_backend")})
            if self.args.get("keyring_backend") == "system":
                top.update({"vault_name": str(uuid.uuid4())})
            self.args["top_level_settings"] = top

    def _init_cluster_vars(self, cluster_vars):
        """
        Makes changes to cluster_vars applicable across architectures
        """
        preferred_python_version = self.args["image"].get(
            "preferred_python_version", "python3"
        )
        cluster_vars["preferred_python_version"] = cluster_vars.get(
            "preferred_python_version", preferred_python_version
        )

        self._add_cluster_vars_args(cluster_vars)

        if self.args.get("postgres_flavour") == "epas":
            k = "epas_redwood_compat"
            cluster_vars[k] = cluster_vars.get(k, self.args.get(k))

        self._add_extra_packages(cluster_vars)

        self._add_source_install(cluster_vars)

    def _add_cluster_vars_args(self, cluster_vars):
        """Add args that belongs to cluster_vars without any change or logic"""
        for k in self.cluster_vars_args():
            val = self.args.get(k)
            if val is not None:
                cluster_vars[k] = cluster_vars.get(k, val)

    def _add_extra_packages(self, cluster_vars):
        """Add extra packages lists to cluster_vars"""

        package_option_vars = {
            "extra_packages": "packages",
            "extra_optional_packages": "optional_packages",
            "extra_postgres_packages": "extra_postgres_packages",
        }

        for e in package_option_vars.keys():
            packages = self.args.get(e)
            if packages is not None:
                var = package_option_vars[e]
                val = {"common": packages}
                cluster_vars[var] = cluster_vars.get(var, val)

    def _add_source_install(self, cluster_vars):
        """Add --install-from-source entries into cluster_vars"""
        sources = self.args.get("install_from_source") or []
        install_from_source = []
        for name in sources:
            self._update_source_refs(name, cluster_vars, install_from_source)

        if install_from_source:
            cluster_vars["install_from_source"] = cluster_vars.get(
                "install_from_source", install_from_source
            )

        if sources:
            top = self.args.get("top_level_settings") or {}
            top.update({"forward_ssh_agent": "yes"})
            self.args["top_level_settings"] = top

    def _update_source_refs(self, name, cluster_vars, install_from_source):
        installable_sources = self.installable_sources()
        ref = None
        if ":" in name:
            (name, ref) = name.split(":", 1)
        name = name.lower()
        entry = installable_sources[name]

        self._check_local_sources(name, ref)

        if name in ["postgres", "2ndqpostgres", "epas"]:
            if ref:
                entry.update({"postgres_git_ref": ref})
            cluster_vars.update(entry)
        elif name == "barman":
            if ref:
                entry.update({"barman_git_ref": ref})
            cluster_vars.update(entry)
        elif name == "pg-backup-api":
            if ref:
                entry.update({"pg_backup_api_git_ref": ref})
            cluster_vars.update(entry)
        elif name in ["patroni", "patroni-edb"]:
            if ref:
                entry.update({"patroni_git_ref": ref})
            cluster_vars.update(entry)
        else:
            if ref:
                entry.update({"git_repository_ref": ref})
            install_from_source.append(entry)

    def _check_local_sources(self, name, ref):
        """Check that we don't fix a ref when using local source"""
        local_sources = self.args.get("local_sources") or {}
        if ref and name in local_sources:
            raise ArchitectureError(
                f"--install-from-source can't guarantee {name}:{ref} while using local source"
                f" directory {local_sources[name].split(':')[0]}"
            )

    def postgres_eol_repos(self, cluster_vars):
        if (
            self.args.get("postgres_version")
            in [
                "9.4",
                "9.5",
                "9.6",
            ]
            and self.args.get("distribution") == "RedHat"
        ):
            if "yum_repositories" not in cluster_vars.keys():
                cluster_vars["yum_repositories"] = {}

            repo_name = "PGDG" + str.replace(self.args.get("postgres_version"), ".", "")
            cluster_vars["yum_repository_list"] = [
                "PGDG",
                "EPEL",
                repo_name,
            ]
            cluster_vars["yum_repositories"][repo_name] = {
                "description": "Archive Postgres {} Repo".format(
                    self.args.get("postgres_version")
                ),
                "baseurl": "https://yum-archive.postgresql.org/{}/redhat/rhel-$releasever-$basearch".format(
                    self.args.get("postgres_version")
                ),
                "file": repo_name,
                "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG",
                "exclude": "python-psycopg2 python2-psycopg2 python3-psycopg2",
                "repo_gpgcheck": "no",
            }

            if self.args.get("bdr_version") == "1":
                cluster_vars["yum_repository_list"].append("EDB")

            if self.args.get("postgres_version") == "9.6":
                DEBUGINFO_SUFFIX = "{}-debuginfo"
                cluster_vars["yum_repositories"][DEBUGINFO_SUFFIX.format(repo_name)] = {
                    "description": "Postgres Debug Info {} Repo".format(
                        self.args.get("postgres_version")
                    ),
                    "baseurl": "https://download.postgresql.org/pub/repos/yum/debug/{}/redhat/rhel-$releasever-$basearch".format(
                        self.args.get("postgres_version")
                    ),
                    "file": DEBUGINFO_SUFFIX.format(repo_name),
                    "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG",
                    "repo_gpgcheck": "yes",
                }
                cluster_vars["yum_repository_list"].append(
                    DEBUGINFO_SUFFIX.format(repo_name)
                )

    def set_2q_repos(self, cluster_vars):
        """Set 2q repos to be empty explicitly if we are on an OS/version combination
        that they don't support."""

        supported_combinations = [
            "RedHat:7",
            "RedHat:8",
            "Rocky:8",
            "AlmaLinux:8",
            "Debian:8",
            "Debian:9",
            "Debian:10",
            "Debian:11",
            "Debian:jessie",
            "Debian:stretch",
            "Debian:buster",
            "Debian:bullseye",
            "Ubuntu:16.04",
            "Ubuntu:18.04",
            "Ubuntu:20.04",
            "Ubuntu:22.04",
            "Ubuntu:xenial",
            "Ubuntu:bionic",
            "Ubuntu:focal",
            "Ubuntu:jammy",
        ]

        distribution = self.args.get("distribution")
        os_version = self.args.get("os_version")

        if (
            distribution
            and os_version
            and distribution + ":" + os_version not in supported_combinations
            and "tpa_2q_repositories" not in cluster_vars
        ):
            cluster_vars["tpa_2q_repositories"] = []

    def default_edb_repos(self, cluster_vars) -> List[str]:
        """Returns the default EDB (i.e., Cloudsmith) repositories we think are
        required for the given cluster, based on postgres_flavour etc. (which
        are required to be set by now)."""

        postgres_flavour = self.args.get("postgres_flavour") or "impossible"

        postgres_repos = {
            "postgresql": ["standard"],
            "edbpge": ["standard"],
            # No matter how the flavour is specified, we translate 'pgextended'
            # into 'edbpge' for all but BDR-Always-ON, for which we would never
            # call this function anyway (see below).
            "pgextended": ["standard", "postgres_extended"],
            "epas": ["enterprise"],
        }

        repos = postgres_repos[postgres_flavour]

        # If you just need Postgres and haven't asked for any other proprietary
        # software, we don't need to require any EDB repos. You'll be fine with
        # just PGDG. For anything else, you can always specify the correct list
        # with --edb-repositories.

        if (
            postgres_flavour == "postgresql"
            and not self.args.get("failover_manager") == "efm"
            and not self.name in ("PGD-Always-ON", "BDR-Always-ON")
            and not self.args.get("enable_pem")
        ):
            repos = []

        return repos

    def update_repos(self, cluster_vars):
        """Define package repositories for the cluster based on the selected
        architecture and Postgres flavour/version."""

        # TPA supports two kinds of repositories: (a) EDB's new Cloudsmith
        # repositories, defined via --edb-repositories; and (b) arbitrary APT or
        # YUM repos, defined by setting {apt,yum}_{repositories,repository_list}
        # in config.yml (not via configure options). PGDG, EPEL, and the legacy
        # EDB repos ({apt,yum}.enterprisedb.com) are defined using this method
        # (see default_{apt,yum}_repositories).
        #
        # EDB's new Cloudsmith repositories are arranged around the different
        # subscription levels available to customers: community360, standard,
        # and enterprise (and postgres_distributed, for the Extreme HA add-on
        # subscription available with either standard or enterprise).
        #
        # The original idea was to provide EDB's builds of supported open-source
        # software in the community360 repo, as an alternative to PGDG packages
        # (which are also fully supported). The standard repo would include the
        # community360 packages, plus some proprietary software (e.g., PGE).
        # The enterprise repo would include everything in community360 and
        # standard, plus EPAS and some other proprietary software.
        #
        # In practice, the standard and enterprise repos follow this layout, but
        # the community360 repo does not contain any packages, and it will take
        # a good while before it becomes a viable alternative to using PGDG. For
        # now, we never use the community360 repo by default; and even if it's
        # explicitly requested, we make sure to include PGDG as well (which we
        # don't do otherwise, e.g., for PGD-Always-ON).
        #
        # Ideally, a new cluster would use only the EDB Cloudsmith repositories
        # if it needed any EDB proprietary software (this is the case for all
        # PGD-Always-ON clusters). If it did not need proprietary software, it
        # would use only PGDG (whose packages remain fully supported).
        #
        # Before the Cloudsmith repositories were introduced, clusters required
        # a mixture of 2Q repositories with PGDG(+EPEL) and the legacy EDB repos
        # (for EPAS/EFM/etc., if used). All supported packages that EDB provide
        # are now available in the Cloudsmith repositories.
        # (Of course, you can still specify different/additional
        # repositories in config.yml, and existing configurations will continue
        # to work as before.)
        #
        # If a user goes to the trouble of specifying an --edb-repositories list
        # (and not just "none" or the flavour-dependent defaults derived later),
        # that wins over everything else.

        edb_repositories = self.args.get("edb_repositories")
        if edb_repositories and edb_repositories != ["none"]:
            cluster_vars.update({"edb_repositories": edb_repositories})
            return

        # If --edb-repositories is specified, we use the list to override the
        # defaults based on postgres_flavour. We translate `none` to [], but do
        # not make any other changes to the given list (no automagic additions
        # to the list, unlike BDR.update_cluster_vars).

        if not edb_repositories:
            edb_repositories = self.default_edb_repos(cluster_vars)
        elif edb_repositories == ["none"]:
            edb_repositories = []

        if edb_repositories:
            cluster_vars.update({"edb_repositories": edb_repositories})

        # In general, if we're using EDB repositories at all, we don't want
        # packages from PGDG, unless we're using community360 as explained
        # above. Note that `--edb-repositories none` means we do want PGDG.

        if edb_repositories and "community360" not in edb_repositories:
            cluster_vars.update(
                {
                    "apt_repository_list": [],
                    "yum_repository_list": ["EPEL"],
                }
            )

    def cluster_vars_args(self):
        """
        Returns the names of any variables set by command-line options that
        belong under cluster_vars
        """
        return [
            "postgres_flavour",
            "postgres_version",
            "tpa_2q_repositories",
            "use_volatile_subscriptions",
            "use_local_repo_only",
            "failover_manager",
            "enable_pg_backup_api",
        ] + ["%s_package_version" % x for x in self.versionable_packages()]

    def versionable_packages(self):
        """
        Returns a list of packages for which --xxx-package-version options
        should be accepted
        """
        return ["postgres", "repmgr", "barman", "pglogical", "bdr", "pgbouncer"]

    def product_repositories(self):
        """
        Returns a list of product names that should be accepted as (part of) the
        arguments to --2Q-repositories
        """
        return [
            "default",
            "2ndqpostgres",
            "bdr2",
            "bdr3",
            "pglogical3",
            "server-ssl-passphrase-callback",
            "postgresql",
            "bdr_enterprise_3_6",
            "livecompare",
            "bdr3_7",
            "pglogical3_7",
            "bdr_enterprise_3_7",
            "harp",
            "bdr3_7-epas",
            "bdr_enterprise_3_7-epas",
            "bdr4",
            "bdr_enterprise_4",
            "bdr_enterprise_4-epas",
            "lasso",
        ]

    def installable_sources(self):
        """
        Returns a map of things that should be accepted as arguments to
        --install-from-source to their corresponding build configuration
        """
        return {
            "postgres": {
                "postgres_installation_method": "src",
                "postgres_git_url": "https://git.postgresql.org/git/postgresql.git",
            },
            "2ndqpostgres": {
                "postgres_installation_method": "src",
                "postgres_git_url": "git@github.com:EnterpriseDB/2ndqpostgres.git",
            },
            "epas": {
                "postgres_installation_method": "src",
                "postgres_git_url": "git@github.com:EnterpriseDB/edbas.git",
            },
            "pglogical3": {
                "name": "pglogical",
                "git_repository_url": "git@github.com:EnterpriseDB/pglogical.git",
                "git_repository_ref": "REL3_7_STABLE",
            },
            "bdr3": {
                "name": "bdr",
                "git_repository_url": "git@github.com:EnterpriseDB/bdr.git",
                "git_repository_ref": "REL3_7_STABLE",
                "build_commands": [
                    "make -f ../../src/bdr/Makefile -s install",
                ],
            },
            "bdr4": {
                "name": "bdr",
                "git_repository_url": "git@github.com:EnterpriseDB/bdr.git",
                "git_repository_ref": "REL_4_STABLE",
                "build_commands": [
                    "make -f ../../src/bdr/Makefile -s install",
                ],
            },
            "bdr5": {
                "name": "bdr",
                "git_repository_url": "git@github.com:EnterpriseDB/bdr.git",
                "build_commands": [
                    "make -f ../../src/bdr/Makefile -s install",
                ],
            },
            "barman": {
                "barman_installation_method": "src",
                "barman_git_url": "git@github.com:EnterpriseDB/barman.git",
            },
            "pg-backup-api": {
                "pg_backup_api_installation_method": "src",
                "pg_backup_api_git_url": "git@github.com:EnterpriseDB/pg-backup-api.git",
            },
            "patroni": {
                "patroni_installation_method": "src",
                "patroni_git_url": "https://github.com/zalando/patroni.git",
            },
            "patroni-edb": {
                "patroni_installation_method": "src",
                "patroni_git_url": "https://github.com/EnterpriseDB/patroni.git",
            },
        }

    def update_cluster_vars(self, cluster_vars):
        """
        Makes architecture-specific changes to cluster_vars if required
        """
        pass

    def _init_instance_defaults(self, instance_defaults):
        """
        Makes changes to instance_defaults applicable across architectures
        """
        if instance_defaults.get("platform") is None:
            instance_defaults["platform"] = self.platform.name
        vars = instance_defaults.get("vars", {})
        if vars.get("ansible_user") is None and "tower_settings" not in self.args:
            vars["ansible_user"] = self.args["image"].get("user", "root")
            instance_defaults["vars"] = vars

    def update_instance_defaults(self, instance_defaults):
        """
        Makes architecture-specific changes to instance_defaults if required
        """
        pass

    def _init_instances(self, instances):
        """
        Makes changes to instances applicable across architectures
        """
        for instance in instances:
            location = instance.get("location", None)
            if isinstance(location, int) and location < len(self.args["locations"]):
                instance["location"] = self.args["locations"][location]["Name"]

    def update_instances(self, instances):
        """
        Makes architecture-specific changes to instances if required
        """
        pass

    ##
    ## Cluster directory creation
    ##

    def generate_configuration(self) -> str:
        """
        Returns the final contents of config.yml
        """
        return self.expand_template("config.yml.j2", self.args)

    def write_configuration(self, configuration: str, force: bool = False) -> None:
        """
        Creates the cluster directory and writes config.yml
        """
        try:
            os.makedirs(self.cluster, exist_ok=force)
            config_path = f"{self.cluster}/config.yml"
            if not os.path.exists(config_path) or force:
                with open(config_path, "w") as cfg:
                    cfg.write(configuration)
        except OSError as e:
            raise ArchitectureError(f"Could not write cluster directory: {str(e)}")

    def setup_local_repo(self):
        """
        Create a directory under cluster/local-repo to contain packages for the
        distribution and version derived from the cluster's selected image().
        """
        try:
            major_version = self.image()["version"].split(".")[0]
            os.makedirs(
                os.path.join(
                    self.cluster, "local-repo", self.image()["os_family"], major_version
                )
            )
        except KeyError:
            raise ArchitectureError(
                f"Warning: Unable to detect OS family and version or image ({self.image().get('name', 'None')})\n"
                f"Please create the '{self.cluster}/local-repo/<os_family>/<version>' directory yourself.\n"
                f"(See docs/src/local-repo.md for details.)",
            )

    def after_configuration(self, force: bool = False) -> None:
        """
        Performs additional actions after config.yml has been written
        """
        self.create_links(force=force)
        if self.args.get("enable_local_repo"):
            try:
                self.setup_local_repo()
            except ArchitectureError as err:
                print(err, file=sys.stderr)
            self.platform.setup_local_repo()
        if not self.args["no_git"]:
            self.setup_git_repository()

    def run_external_command(self, command) -> None:
        p = subprocess.Popen(
            command,
            cwd=self.cluster,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        (_, errstr) = p.communicate()
        if p.returncode != 0:
            raise ExternalCommandError(errstr)

    def setup_git_repository(self) -> None:
        """
        Creates a git repository for the cluster directory, adds the files and links that have
        been created to it, and adds a remote repository for Tower if one was given on the command line.
        """
        try:
            subprocess.run(
                ["git", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except:
            return

        try:
            self.run_external_command(
                ["git", "init"],
            )
        except ExternalCommandError as ece:
            raise ArchitectureError(
                f"Failed to initialise git repository: { ece.errstr }"
            )

        try:
            self.run_external_command(
                ["git", "checkout", "-b", self.args["cluster_name"]],
            )
        except ExternalCommandError as ece:
            raise ArchitectureError(f"Failed to check out git branch: { ece.errstr }")

        if self.args.get("tower_git_repository"):
            try:
                self.run_external_command(
                    [
                        "git",
                        "remote",
                        "add",
                        "tower",
                        self.args["tower_git_repository"],
                    ],
                )
            except ExternalCommandError as ece:
                raise ArchitectureError(
                    f"Failed to add remote repository: { ece.errstr }"
                )

        files = [
            f
            for f in ["config.yml", *self.links_to_create()]
            if os.path.exists(os.path.join(self.cluster, f))
        ]

        try:
            self.run_external_command(
                ["git", "add"] + files,
            )
        except ExternalCommandError as ece:
            raise ArchitectureError(f"Failed to add files to git: { ece.errstr }")

        try:
            self.run_external_command(
                [
                    "git",
                    "commit",
                    "-m",
                    f'Initial configuration for cluster { self.args["cluster_name"] }',
                    "-m",
                    " ".join(sys.argv),
                ],
            )
        except ExternalCommandError as ece:
            raise ArchitectureError(f"Failed to commit files to git: { ece.errstr }")

        try:
            self.run_external_command(
                ["git", "notes", "add", "-m", "Created by TPA"],
            )
        except ExternalCommandError as ece:
            raise ArchitectureError(f"Failed to create git note: { ece.errstr }")

    def create_links(self, force: bool = False) -> None:
        """
        Creates links from the cluster directory to the architecture directory
        (e.g., for deploy.yml and commands; see links_to_create below)
        """
        for link in self.links_to_create():
            # If we're provisioning for AAC/Tower, we copy files into the
            # cluster directory (to be checked in to a git repository),
            # instead of generating symlinks to our local $TPA_DIR.
            if "tower_settings" in self.args:
                if os.path.isfile(os.path.join(self.dir, link)):
                    shutil.copy(
                        os.path.join(self.dir, link), os.path.join(self.cluster, link)
                    )
                elif os.path.isdir(os.path.join(self.dir, link)):
                    shutil.copytree(
                        os.path.join(self.dir, link), os.path.join(self.cluster, link)
                    )
            else:
                update_symlinks_recursively(
                    os.path.join(self.dir, link),
                    os.path.join(self.cluster, link),
                    force,
                )

    def links_to_create(self) -> List[str]:
        """
        Returns a list of targets to create_links() for
        """
        return ["deploy.yml", "commands", "tests"]

    ##
    ## Template processing
    ##

    def template_directories(self):
        """
        Returns a list of directories in which templates may be found for the
        current architecture: Architecture-Name/templates and lib/templates by
        default.
        """
        return ["%s/templates" % x for x in [self.dir, self.lib]]

    def layout_names(self):
        """
        Returns a list of template names that can be selected with the --layout
        option (apart from the default main.yml.j2). May be empty if the
        architecture provides no selectable layouts.
        """
        with Path(self.template_directories()[0]) as path:
            return list(
                map(
                    lambda t: os.path.basename(t.name.replace(".yml.j2", "")),
                    path.glob("layouts/*.yml.j2"),
                )
            )

    def default_layout_name(self):
        """
        Returns the (base)name of the default layout for this architecture, or
        None if the architecture does not support layouts or the default is not
        known (main.yml.j2 should be symlinked to layouts/default.yml.j2).
        """
        template_dir = self.template_directories()[0]
        main_template = f"{template_dir}/main.yml.j2"
        if os.path.islink(main_template):
            return os.path.basename(os.readlink(main_template)).replace(".yml.j2", "")

    def load_yaml(self, filename, vars, loader=None):
        """
        Takes a template filename and some vars, expands the template, parses
        the output as YAML, and returns the resulting data structure
        """
        text = self.expand_template(filename, vars, loader)
        return yaml.load(text, Loader=yaml.FullLoader)

    def expand_template(self, filename, vars, loader=None):
        """
        Takes a template filename and some args and returns the template output
        """
        loader = loader or self.loader()
        templar = Templar(loader=loader, variables=vars)
        template = loader._tpaexec_get_template(filename)
        return templar.do_template(template)

    def loader(self, basedirs=None):
        """
        Returns a template loader object that looks for templates in the
        architecture's template_directories(). If no matching template is found
        in those directories and an absolute path to an existing file is given,
        the loader will return the contents of that template directly.
        """

        class MinimalLoader(object):
            _basedirs = []

            def __init__(self, basedirs):
                self._basedirs = basedirs

            def get_basedir(self):
                return self._basedirs[0]

            def _tpaexec_get_template(self, filename):
                for d in self._basedirs:
                    t = "%s/%s" % (d, filename)
                    if os.path.exists(t):
                        return io.open(t, "r", encoding="utf-8").read()
                if filename.startswith("/") and os.path.exists(filename):
                    return io.open(filename, "r", encoding="utf-8").read()
                return "{}"

        return MinimalLoader(basedirs or self.template_directories())


def update_symlinks_recursively(source, destination, force):
    """
    Update symlinks from source to destination path recursively.

    Args:
        source: Directory path containing files/directories you want to link
        destination: Path where the symlinks need to be created
        force: Overwrite existing links if true

    Returns: None if source does not exist

    """
    if not os.path.exists(source):
        return
    elif os.path.isdir(source):
        if not os.path.exists(destination):
            os.mkdir(destination)
        for ls_link in os.listdir(source):
            update_symlinks_recursively(
                os.path.join(source, ls_link), os.path.join(destination, ls_link), force
            )
    else:
        if force:
            try:
                os.unlink(destination)
            except:
                pass

        os.symlink(source, destination)
