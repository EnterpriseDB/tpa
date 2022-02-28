#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

import sys, os, io
import subprocess
import argparse
import yaml
import glob
import re

from typing import List

from ansible.template import Templar
from ansible.utils.vars import merge_hash
from functools import reduce
from .platform import Platform


class Architecture(object):
    """
    This is the base class for TPA architectures, and it knows how to generate a
    configuration based on architecture-specific defaults defined by subclasses,
    as well as user input in the form of command-line options.
    """

    def __init__(self):
        """
        We expect this constructor to be invoked via a subclass defined in
        architectures/Xyzzy/configure; self.name then becomes 'Xyzzy'. It
        creates a Platform object corresponding to any «--platform x» on the
        command-line.
        """
        self.dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.lib = os.path.realpath("%s/../lib" % self.dir)
        self.name = os.path.basename(self.dir)
        self.platform = Platform.load(sys.argv[1:], arch=self)

    def configure(self):
        """
        Obtains command-line arguments based on the selected architecture and
        platform, gives the architecture and platform a chance to process the
        configuration information, and generates a cluster configuration.
        """
        self.args = self.arguments()
        self.validate_arguments(self.args)
        self.process_arguments(self.args)
        configuration = self.generate_configuration()
        self.write_configuration(configuration)
        self.after_configuration()

    ##
    ## Command-line parsing
    ##

    def arguments(self):
        """
        Returns data obtained from command-line arguments
        """
        return vars(self.argument_parser().parse_args())

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
                choices=self.layout_names(),
                default=self.default_layout_name(),
                help="optional architecture-specific layout selection",
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

        g = p.add_argument_group("software selection")
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
        g.add_argument(
            "--epas",
            action="store_const",
            const="epas",
            dest="postgresql_flavour",
            help="Install EDB Postgres Advanced Server (EPAS)",
        )
        g.add_argument(
            "--no-redwood",
            "--no-redwood-compat",
            action="store_false",
            dest="epas_redwood_compat",
            help="Install EDB Postgres Advanced Server (EPAS) without Oracle compatibility features",
        )
        g.add_argument(
            "--2q",
            "--2ndq",
            "--2ndqpostgres",
            action="store_const",
            const="2q",
            dest="postgresql_flavour",
            help="Install 2ndQuadrant Postgres for BDR EE (2ndQPostgres)",
        )
        g.add_argument(
            "--postgres-flavour",
            dest="postgresql_flavour",
            choices=["2q", "epas", "postgresql"],
        )
        g.add_argument(
            "--postgres-version",
            choices=["9.4", "9.5", "9.6", "10", "11", "12", "13", "14"],
        )
        g.add_argument(
            "--use-volatile-subscriptions",
            action="store_true",
        )
        g.add_argument(
            "--2Q-repositories",
            dest="tpa_2q_repositories",
            nargs="+",
            metavar="source/name/maturity",
        )
        for pkg in self.versionable_packages():
            g.add_argument("--%s-package-version" % pkg, metavar="VER")
        g.add_argument(
            "--extra-postgres-packages",
            nargs="+",
            metavar="NAME",
        )
        g.add_argument("--extra-packages", nargs="+", metavar="NAME")
        g.add_argument("--extra-optional-packages", nargs="+", metavar="NAME")

        g.add_argument("--install-from-source", nargs="+", metavar="NAME")
        g.add_argument(
            "--enable-efm", action="store_const", const="efm", dest="failover_manager"
        )

        g = p.add_argument_group("volume sizes in GB")
        for vol in ["root", "barman", "postgres"]:
            g.add_argument("--%s-volume-size" % vol, type=int, metavar="N")

        g = p.add_argument_group("subnet selection")
        g.add_argument("--subnet")
        g.add_argument("--subnet-pattern", metavar="PATTERN")
        g.add_argument("--exclude-subnets-from", metavar="DIR")

        g = p.add_argument_group("hostname selection")
        g.add_argument("--hostnames-from", metavar="FILE")
        g.add_argument("--hostnames-pattern", metavar="PATTERN")
        g.add_argument("--hostnames-sorted-by", metavar="OPTION")
        g.add_argument("--hostnames-unsorted", action="store_true")

        g = p.add_argument_group("locations")
        g.add_argument("--location-names", metavar="LOCATION", nargs="+")

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
        # Validate arguments to --2Q-repositories
        repos = args.get("tpa_2q_repositories") or []
        for r in repos:
            errors = []
            parts = r.split("/")
            if len(parts) == 3:
                (source, name, maturity) = parts
                if source not in ["ci-spool", "products", "dl"]:
                    errors.append(
                        "unknown source '%s' (try 'dl', 'products', or 'ci-spool')"
                        % source
                    )
                if name not in self.product_repositories():
                    errors.append("unknown product name '%s'" % name)
                if maturity not in ["snapshot", "testing", "release"]:
                    errors.append(
                        "unknown maturity '%s' (try 'release', 'testing', or 'snapshot')"
                        % maturity
                    )
            else:
                errors.append("invalid name (expected source/product/maturity)")

            if errors:
                for e in errors:
                    print("ERROR: repository '%s' has %s" % (r, e), file=sys.stderr)
                sys.exit(-1)

        # Validate arguments to --install-from-source
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
            for e in errors:
                print("ERROR: --install-from-source %s" % (e), file=sys.stderr)
            sys.exit(-1)

        if (
            args.get("epas_redwood_compat") == False
            and args.get("postgresql_flavour") != "epas"
        ):
            print(
                "ERROR: You can specify --no-redwood only when using --epas",
                file=sys.stderr,
            )
            sys.exit(-1)

        self.platform.validate_arguments(args)

    def process_arguments(self, args):
        """
        Augment arguments from the command-line with enough additional
        information (based on the selected architecture and platform) to
        generate config.yml
        """

        # At this point, args is what the command-line parser gave us, i.e., a
        # combination of values specified on the command-line and defaults set
        # by the architecture. Now we start augmenting that information.

        self.cluster = re.sub("/*$", "", args["cluster"])
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
        args["hostnames"] = self.hostnames(self.num_instances())

        # Figure out how to get the desired distribution.
        args["image"] = self.image()

        # Figure out the basic structure of the cluster.
        self.load_topology(args)

        # Now that main.yml.h2 has been loaded, and we have the initial set of
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

        cluster_vars = args.get("cluster_vars", {})
        self._init_cluster_vars(cluster_vars)
        self.update_cluster_vars(cluster_vars)
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
            l = i.get("location")
            if l is not None:
                locations[l] = 1
        return len(locations)

    def hostnames(self, num):
        """
        Returns an array containing 'zero' followed by the requested number of
        hostnames, so that templates can assign hostnames[i] to node[i] without
        regard to the fact that we number nodes starting from 1
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
            print(stderr.strip(), file=sys.stderr)
            sys.exit(-1)

        return ["zero"] + stdout.strip().split(" ")

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

    def subnets(self, num):
        """
        Returns the requested number of subnets
        """

        # If --subnet forced a single subnet, we return an array with that one
        # subnet in it, regardless of the number of subnets that were requested
        subnet = self.args.get("subnet")
        if subnet is not None:
            return [subnet]

        env = {}
        for arg in ["exclude_subnets_from", "subnet_pattern"]:
            if self.args[arg] is not None:
                env[arg.upper()] = self.args[arg]

        popen_params = {}

        if int(str(sys.version_info.major) + str(sys.version_info.minor)) >= 36:
            popen_params["encoding"] = sys.getdefaultencoding()

        p = subprocess.Popen(
            ["%s/subnets" % self.lib, str(num)],
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **popen_params,
        )
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            print(stderr.strip(), file=sys.stderr)
            sys.exit(-1)

        return stdout.strip().split(" ")

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

    def _init_cluster_vars(self, cluster_vars):
        """
        Makes changes to cluster_vars applicable across architectures
        """
        cluster_vars["preferred_python_version"] = cluster_vars.get(
            "preferred_python_version", "python3"
        )

        for k in self.cluster_vars_args():
            val = self.args.get(k)
            if val is not None:
                cluster_vars[k] = cluster_vars.get(k, val)

        if self.args.get("postgresql_flavour") == "epas":
            k = "epas_redwood_compat"
            cluster_vars[k] = cluster_vars.get(k, self.args.get(k))

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

        sources = self.args.get("install_from_source") or []
        local_sources = self.args.get("local_sources") or {}
        installable_sources = self.installable_sources()
        install_from_source = []
        for name in sources:
            ref = None
            if ":" in name:
                (name, ref) = name.split(":", 1)
            name = name.lower()
            entry = installable_sources[name]

            if ref and name in local_sources:
                print(
                    "ERROR: --install-from-source can't guarantee %s:%s while using local source directory %s"
                    % (name, ref, local_sources[name].split(":")[0]),
                    file=sys.stderr,
                )
                sys.exit(-1)

            if name in ["postgres", "2ndqpostgres"]:
                if ref:
                    entry.update({"postgres_git_ref": ref})
                cluster_vars.update(entry)
            elif name == "barman":
                if ref:
                    entry.update({"barman_git_ref": ref})
                cluster_vars.update(entry)
            else:
                if ref:
                    entry.update({"git_repository_ref": ref})
                install_from_source.append(entry)

        if install_from_source:
            cluster_vars["install_from_source"] = cluster_vars.get(
                "install_from_source", install_from_source
            )

        if sources:
            top = self.args.get("top_level_settings") or {}
            top.update({"forward_ssh_agent": "yes"})
            self.args["top_level_settings"] = top

    def cluster_vars_args(self):
        """
        Returns the names of any variables set by command-line options that
        belong under cluster_vars
        """
        return [
            "postgresql_flavour",
            "postgres_version",
            "tpa_2q_repositories",
            "use_volatile_subscriptions",
            "failover_manager",
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
                "build_commands": [
                    "make -f ../../src/bdr/Makefile -s install",
                ],
            },
            "autoscale": {
                "name": "autoscale",
                "git_repository_url": "git@github.com:EnterpriseDB/autoscale.git",
                "build_commands": [
                    "make -f ../../src/autoscale/Makefile -s install",
                ],
            },
            "barman": {
                "barman_installation_method": "src",
                "barman_git_url": "git@github.com:EnterpriseDB/barman.git",
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
        if vars.get("ansible_user") is None:
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

    def write_configuration(self, configuration: str) -> None:
        """
        Creates the cluster directory and writes config.yml
        """
        try:
            os.mkdir(self.cluster)
            with open("%s/config.yml" % self.cluster, "w") as cfg:
                cfg.write(configuration)
        except OSError as e:
            print("Could not write cluster directory: %s" % str(e), file=sys.stderr)
            sys.exit(-1)

    def after_configuration(self) -> None:
        """
        Performs additional actions after config.yml has been written
        """
        self.create_links()

    def create_links(self) -> None:
        """
        Creates links from the cluster directory to the architecture directory
        (e.g., for deploy.yml and commands; see links_to_create below)
        """
        for l in self.links_to_create():
            src = "%s/%s" % (self.dir, l)
            dest = "%s/%s" % (self.cluster, l)
            if not os.path.exists(src):
                continue
            elif not os.path.isdir(src):
                os.symlink(src, dest)
            else:
                os.mkdir(dest)
                for l in os.listdir(src):
                    os.symlink("%s/%s" % (src, l), "%s/%s" % (dest, l))

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
        # glob.glob()'s root_dir parameter was introduced only in 3.10
        oldcwd = os.getcwd()
        os.chdir(self.template_directories()[0])
        layouts = list(
            map(
                lambda t: os.path.basename(t.replace(".yml.j2", "")),
                glob.glob("layouts/*.yml.j2"),
            )
        )
        os.chdir(oldcwd)
        return layouts

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