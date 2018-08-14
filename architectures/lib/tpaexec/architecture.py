#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os, io
import subprocess
import argparse
import dircache
import yaml

from ansible.template import Templar
from tpaexec.platform import Platform

class Architecture(object):
    # We expect this constructor to be invoked via a subclass defined in
    # architectures/Xyzzy/configure; self.name then becomes 'Xyzzy'. It creates
    # a Platform object corresponding to any «--platform x» on the command-line.
    def __init__(self):
        self.dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.lib = os.path.realpath('%s/../lib' % self.dir)
        self.name = os.path.basename(self.dir)
        self.platform = Platform.load(sys.argv[1:], arch=self)

    # Obtains command-line arguments based on the selected architecture and
    # platform, gives the architecture and platform a chance to process the
    # configuration information, and generates a cluster configuration.
    def configure(self):
        self.args = self.arguments()
        self.process_arguments(self.args)
        configuration = self.generate_configuration()
        self.write_configuration(configuration)
        self.after_configuration()

    ##
    ## Command-line parsing
    ##

    # Returns data obtained from command-line arguments
    def arguments(self):
        return vars(self.argument_parser().parse_args())

    # Returns an ArgumentParser object configured to accept the options relevant
    # to the selected architecture and platform
    def argument_parser(self):
        prog = 'tpaexec configure'
        p = argparse.ArgumentParser(
            prog=prog,
            usage='%s <cluster> --architecture %s [--help | …options…]' % (prog, self.name)
        )
        p.add_argument('cluster', help='path to cluster directory')
        self.add_options(p)
        self.set_defaults(p)
        return p

    # Adds any relevant options to the parser object
    def add_options(self, p):
        g = p.add_argument_group('architecture and platform selection')
        g.add_argument(
            '--architecture', '-a', required=True, choices=[self.name],
            help='currently selected architecture'
        )
        g.add_argument(
            '--platform', default='aws', choices=self.supported_platforms(),
            help='platforms supported by %s (selected: %s)' % (self.name, self.platform.name)
        )

        # Options relevant to this architecture
        g = p.add_argument_group('%s architecture options' % self.name)
        self.add_architecture_options(p, g)

        # Options relevant to the selected platform
        g = p.add_argument_group('%s platform options' % self.platform.name)
        self.platform.add_platform_options(p, g)

        g = p.add_argument_group('cluster tags')
        g.add_argument('--owner')

        g = p.add_argument_group('software selection')
        labels = self.platform.supported_distributions()
        label_opts = {'choices': labels} if labels else {}
        default_label = self.platform.default_distribution()
        if default_label:
            label_opts['default'] = default_label
        elif labels and len(labels) == 1:
            label_opts['default'] = labels[0]
        else:
            label_opts['required'] = True
        g.add_argument(
            '--distribution', '--os', dest='distribution',
            metavar='LABEL', **label_opts
        )
        g.add_argument(
            '--postgres-version', choices=['9.4', '9.5', '9.6', '10', '11']
        )
        g.add_argument(
            '--2Q-repositories', dest='tpa_2q_repositories', nargs='+',
            metavar='source/name/maturity',
        )
        for pkg in self.versionable_packages():
            g.add_argument('--%s-package-version' % pkg, metavar='VER')

        g = p.add_argument_group('volume sizes in GB')
        for vol in ['root', 'barman', 'postgres']:
            g.add_argument('--%s-volume-size' % vol, type=int, metavar='N')
        p.set_defaults(
            root_volume_size=16, postgres_volume_size=16, barman_volume_size=32
        )

        g = p.add_argument_group('subnet selection')
        g.add_argument('--subnet')
        g.add_argument('--subnet-pattern', metavar='PATTERN')
        g.add_argument('--exclude-subnets-from', metavar='DIR')

        g = p.add_argument_group('hostname selection')
        g.add_argument('--hostnames-from', metavar='FILE')
        g.add_argument('--hostnames-pattern', metavar='PATTERN')
        g.add_argument('--hostnames-sorted-by', metavar='OPTION')

    # Adds architecture-specific options to the (relevant group in the) parser
    # (subclasses are expected to override this).
    def add_architecture_options(self, p, g):
        pass

    # Set default values for command-line options
    def set_defaults(self, p):
        argument_defaults = Architecture.argument_defaults(self)
        argument_defaults.update(self.argument_defaults())
        p.set_defaults(**argument_defaults)

    # Returns a dict of defaults for the applicable options
    def argument_defaults(self):
        return {
            'root_volume_size': 16,
            'barman_volume_size': 32,
            'postgres_volume_size': 16,
        }

    # Returns the default platform for this architecture (i.e., the platform
    # that will be used if no «--platform x» is specified)
    def default_platform(self):
        return 'aws'

    # Returns a list of platforms supported by this architecture
    def supported_platforms(self):
        return Platform.all_platforms()

    ##
    ## Cluster configuration
    ##

    # Augment arguments from the command-line with enough additional information
    # (based on the selected architecture and platform) to generate config.yml
    def process_arguments(self, args):
        # At this point, args is what the command-line parser gave us, i.e., a
        # combination of values specified on the command-line and defaults set
        # by the architecture. Now we start augmenting that information.

        self.cluster = args['cluster']
        args['cluster_name'] = self.cluster_name()

        # The architecture's num_instances() method should work by this point,
        # so that we can generate the correct number of hostnames.
        args['hostnames'] = self.hostnames(self.num_instances())

        # The platform gets to decide what image parameters are required to get
        # the desired distribution
        args['image'] = self.platform.image(self.args['distribution'])

        # The architecture's templates/main.yml.j2 defines the overall topology
        # of the cluster, and must be written so that we can expand it based on
        # the correct number of hostnames and information from the command-line.
        y = self.load_yaml('main.yml.j2', args)
        if y is not None:
            args.update(y)

        # Now that main.yml.h2 has been loaded, and we have the initial set of
        # instances[] defined, num_locations() should work, and we can generate
        # the necessary number of subnets.
        args['subnets'] = self.subnets(self.num_locations())

        cluster_tags = args.get('cluster_tags', {})
        self.update_cluster_tags(cluster_tags)
        self.platform.update_cluster_tags(cluster_tags, args)
        args['cluster_tags'] = cluster_tags

        cluster_vars = args.get('cluster_vars', {})
        Architecture.update_cluster_vars(self, cluster_vars)
        self.update_cluster_vars(cluster_vars)
        self.platform.update_cluster_vars(cluster_vars, args)
        args['cluster_vars'] = cluster_vars

        instance_defaults = args.get('instance_defaults', {})
        Architecture.update_instance_defaults(self, instance_defaults)
        self.update_instance_defaults(instance_defaults)
        self.platform.update_instance_defaults(instance_defaults, args)
        args['instance_defaults'] = instance_defaults

        instances = args.get('instances', {})
        self.update_instances(instances)
        self.platform.update_instances(instances, args)
        args['instances'] = instances

        self.platform.process_arguments(args)

    # Returns a name for the cluster
    def cluster_name(self):
        return os.path.basename(self.cluster)

    # Returns the number of instances required (which may be known beforehand,
    # or based on a --num-instances option, etc.)
    def num_instances(self):
        return self.args['num_instances']

    # Returns the number of locations required by this architecture
    def num_locations(self):
        locations = {}
        for i in self.args['instances']:
            l = i.get('location')
            if l is not None:
                locations[l] = 1
        return len(locations)

    # Returns an array containing 'zero' followed by the requested number of
    # hostnames, so that templates can assign hostnames[i] to node[i] without
    # regard to the fact that we number nodes starting from 1
    def hostnames(self, num):
        env = {}
        for arg in ['hostnames_from', 'hostnames_pattern', 'hostnames_sorted_by']:
            if self.args[arg] is not None:
                env[arg.upper()] = self.args[arg]

        p = subprocess.Popen(
            ['%s/hostnames' % self.lib, str(num)], stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env
        )
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            print(stderr.strip(), file=sys.stderr)
            sys.exit(-1)

        return ['zero'] + stdout.strip().split(' ')

    # Returns the requested number of subnets
    def subnets(self, num):
        # If --subnet forced a single subnet, we return an array with that one
        # subnet in it, regardless of the number of subnets that were requested
        subnet = self.args.get('subnet')
        if subnet is not None:
            return [subnet]

        env = {}
        for arg in ['exclude_subnets_from', 'subnet_pattern']:
            if self.args[arg] is not None:
                env[arg.upper()] = self.args[arg]

        p = subprocess.Popen(
            ['%s/subnets' % self.lib, str(num)], stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env
        )
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            print(stderr.strip(), file=sys.stderr)
            sys.exit(-1)

        return stdout.strip().split(' ')

    # Makes architecture-specific changes to cluster_tags if required
    def update_cluster_tags(self, cluster_tags):
        pass

    # Makes architecture-specific changes to cluster_vars if required
    def update_cluster_vars(self, cluster_vars):
        for k in self.cluster_vars_args():
            val = self.args.get(k)
            if val is not None:
                cluster_vars[k] = val

    # Returns the names of any variables set by command-line options that belong
    # under cluster_vars
    def cluster_vars_args(self):
        return [
            'tpa_2q_repositories', 'postgres_version',
        ] + [
            '%s_package_version' % x for x in self.versionable_packages()
        ]

    # Returns a list of packages for which --xxx-package-version options should
    # be accepted
    def versionable_packages(self):
        return [
            'postgres', 'repmgr', 'barman', 'pglogical', 'bdr', 'pgbouncer'
        ]

    # Makes architecture-specific changes to instance_defaults if required
    def update_instance_defaults(self, instance_defaults):
        if instance_defaults.get('platform') is None:
            instance_defaults['platform'] = self.platform.name
        vars = instance_defaults.get('vars', {})
        if vars.get('ansible_user') is None:
            vars['ansible_user'] = self.args['image'].get('user', 'root')
            instance_defaults['vars'] = vars

    # Makes architecture-specific changes to instances if required
    def update_instances(self, instances):
        pass

    ##
    ## Cluster directory creation
    ##

    # Returns the final contents of config.yml
    def generate_configuration(self):
        return self.expand_template('config.yml.j2', self.args)

    # Creates the cluster directory and writes config.yml
    def write_configuration(self, configuration):
        try:
            os.mkdir(self.cluster)
            with open('%s/config.yml' % self.cluster, 'w') as cfg:
                cfg.write(configuration)
        except OSError as e:
            print('Could not write cluster directory: %s' % str(e), file=sys.stderr)
            sys.exit(-1)

    # Performs additional actions after config.yml has been written
    def after_configuration(self):
        self.create_links()

    # Creates links from the cluster directory to the architecture directory
    # (e.g., for deploy.yml and commands; see links_to_create below)
    def create_links(self):
        for l in self.links_to_create():
            src = '%s/%s' % (self.dir, l)
            dest = '%s/%s' % (self.cluster, l)
            if not os.path.exists(src):
                continue
            elif not os.path.isdir(src):
                os.symlink(src, dest)
            else:
                os.mkdir(dest)
                for l in dircache.listdir(src):
                    os.symlink('%s/%s' % (src, l), '%s/%s' % (dest, l))

    # Returns a list of targets to create_links() for
    def links_to_create(self):
        return ['deploy.yml', 'commands']

    ##
    ## Template processing
    ##

    # Takes a template filename and some args and returns the template output
    def expand_template(self, filename, vars):
        return self.templar(vars).do_template(self.template(filename))

    # Takes a template filename and some args, expands the template, parses the
    # output as YAML and returns the resulting data structure
    def load_yaml(self, filename, args):
        return yaml.load(self.expand_template(filename, args))

    # Returns the contents of the given template file from the architecture's
    # templates/ directory (if it exists there) or the lib/templates directory,
    # or an empty string if the given template is not found in either place.
    def template(self, filename):
        return self.loader()._tpaexec_get_template(filename)

    # Returns an Ansible Templar object (the use of our filter/lookup/test
    # plugins depends on ANSIBLE_FILTER_PLUGINS etc. being set)
    def templar(self, vars):
        return Templar(loader=self.loader(), variables=vars)

    # Returns a template loader object that looks for templates in the
    # architecture's templates/ directory as well as lib/templates
    def loader(self):
        class MinimalLoader(object):
            _basedir = []
            def __init__(self, basedir):
                self._basedir = basedir
            def get_basedir(self):
                return self._basedir
            def _tpaexec_get_template(self, filename):
                for d in self._basedir:
                    t = '%s/%s' % (d, filename)
                    if os.path.exists(t):
                        return io.open(t, 'r').read()
                return ''
        return MinimalLoader(['%s/templates' % x for x in [self.dir, self.lib]])
