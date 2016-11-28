#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''Imports AWS EC2 regions and zones.

At the moment the data is hard-coded output fromaws ec2 describe*, though
eventually we'll want this periodically updated with fresh data.
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging
from uuid import uuid5, NAMESPACE_URL

from django.db import migrations


logger = logging.getLogger(__name__)


def gen_uuid(object_type, *unique_name):
    name = "http://2ndquadrant.com/api/v1/tpa/%s/%s".encode('utf-8') \
        % (object_type.lower(), '-'.join(unique_name))

    return uuid5(NAMESPACE_URL, str(name))


def load_aws_data(apps, schema_editor):
    Provider = apps.get_model('tpa', 'Provider')
    Region = apps.get_model('tpa', 'Region')
    Zone = apps.get_model('tpa', 'Zone')
    InstanceType = apps.get_model('tpa', 'InstanceType')

    db_alias = schema_editor.connection.alias

    providers = [
        Provider(uuid=gen_uuid('provider', uuid_suffix),
                 name=name,
                 description=description)
            for (uuid_suffix, name, description) in PROVIDERS
    ]
    Provider.objects.using(db_alias).bulk_create(providers)

    regions = [
        Region(uuid=gen_uuid('region', "EC2", name),
               provider=[p for p in providers if p.name == 'EC2'][0],
               name=name,
               description='')
            for name in REGIONS
    ]
    Region.objects.using(db_alias).bulk_create(regions)

    zones = [
        Zone(uuid=gen_uuid('zone', "EC2", region, name),
             name=name,
             region=[r for r in regions if r.name == region][0],
             description='')
            for (region, name) in ZONES
    ]
    Zone.objects.using(db_alias).bulk_create(zones)

    instance_types = [
        InstanceType(uuid=gen_uuid('instance_type', "EC2",
                                   region, zone.name, type_name),
                     name=type_name,
                     zone=zone,
                     description='')
            for zone in zones
                for type_name in INSTANCE_TYPES
    ]
    InstanceType.objects.using(db_alias).bulk_create(instance_types)



class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('tpa', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(load_aws_data),
    ]


PROVIDERS = [
    # uuid_suffix, name, description
    ('ec2', 'EC2', 'AWS EC2'),
]

REGIONS = [
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "eu-central-1",
    "eu-west-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
]

# raw output from describe-availability-zones
ZONES = [
	("ap-south-1",     "ap-south-1a"),
	("ap-south-1",     "ap-south-1b"),
	("eu-west-1",      "eu-west-1a"),
	("eu-west-1",      "eu-west-1b"),
	("eu-west-1",      "eu-west-1c"),
	("ap-northeast-2", "ap-northeast-2a"),
	("ap-northeast-2", "ap-northeast-2c"),
	("ap-northeast-1", "ap-northeast-1a"),
	("ap-northeast-1", "ap-northeast-1b"),
	("ap-northeast-1", "ap-northeast-1c"),
	("sa-east-1",      "sa-east-1a"),
	("sa-east-1",      "sa-east-1b"),
	("sa-east-1",      "sa-east-1c"),
	("ap-southeast-1", "ap-southeast-1a"),
	("ap-southeast-1", "ap-southeast-1b"),
	("ap-southeast-2", "ap-southeast-2a"),
	("ap-southeast-2", "ap-southeast-2b"),
	("ap-southeast-2", "ap-southeast-2c"),
	("eu-central-1",   "eu-central-1a"),
	("eu-central-1",   "eu-central-1b"),
	("us-east-1",      "us-east-1a"),
	("us-east-1",      "us-east-1b"),
	("us-east-1",      "us-east-1c"),
	("us-east-1",      "us-east-1d"),
	("us-east-1",      "us-east-1e"),
	("us-east-2",      "us-east-2a"),
	("us-east-2",      "us-east-2b"),
	("us-east-2",      "us-east-2c"),
	("us-west-1",      "us-west-1a"),
	("us-west-1",      "us-west-1b"),
	("us-west-1",      "us-west-1c"),
	("us-west-2",      "us-west-2a"),
	("us-west-2",      "us-west-2b"),
	("us-west-2",      "us-west-2c"),
]

# From: http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-spot-price-history.html

INSTANCE_TYPES = '''
    t1.micro
    t2.nano
    t2.micro
    t2.small
    t2.medium
    t2.large
    m1.small
    m1.medium
    m1.large
    m1.xlarge
    m3.medium
    m3.large
    m3.xlarge
    m3.2xlarge
    m4.large
    m4.xlarge
    m4.2xlarge
    m4.4xlarge
    m4.10xlarge
    m4.16xlarge
    m2.xlarge
    m2.2xlarge
    m2.4xlarge
    cr1.8xlarge
    r3.large
    r3.xlarge
    r3.2xlarge
    r3.4xlarge
    r3.8xlarge
    x1.16xlarge
    x1.32xlarge
    i2.xlarge
    i2.2xlarge
    i2.4xlarge
    i2.8xlarge
    hi1.4xlarge
    hs1.8xlarge
    c1.medium
    c1.xlarge
    c3.large
    c3.xlarge
    c3.2xlarge
    c3.4xlarge
    c3.8xlarge
    c4.large
    c4.xlarge
    c4.2xlarge
    c4.4xlarge
    c4.8xlarge
    cc1.4xlarge
    cc2.8xlarge
    g2.2xlarge
    g2.8xlarge
    cg1.4xlarge
    p2.xlarge
    p2.8xlarge
    p2.16xlarge
    d2.xlarge
    d2.2xlarge
    d2.4xlarge
    d2.8xlarge'''.split()
