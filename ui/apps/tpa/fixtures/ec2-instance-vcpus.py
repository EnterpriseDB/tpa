#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

'''
'''

from __future__ import unicode_literals, absolute_import, print_function

import logging


logger = logging.getLogger(__name__)


VCPUS = [s.split() for s in '''
t1.micro	1
t2.micro	1
t2.small	1
t2.medium	2
t2.large	2
t2.xlarge 4
t2.2xlarge 8
m1.small	1
m1.medium	1
m1.large	2
m1.xlarge	4
m2.xlarge	2
m2.2xlarge	4
m2.4xlarge	8
m3.medium	1
m3.large	1
m3.xlarge	2
m3.2xlarge	4
m4.large	1
m4.xlarge	2
m4.2xlarge	4
m4.4xlarge	8
m4.10xlarge	20
m4.16xlarge	32
c1.medium	2
c1.xlarge	8
cc2.8xlarge	16
cg1.4xlarge	8
cr1.8xlarge	16
c3.large	1
c3.xlarge	2
c3.2xlarge	4
c3.4xlarge	8
c3.8xlarge	16
c4.large	1
c4.xlarge	2
c4.2xlarge	4
c4.4xlarge	8
c4.8xlarge	18
hi1.4xlarge	8
hs1.8xlarge	8
g2.2xlarge	16
x1.16xlarge	32
x1.32xlarge	64
r4.large 1
r4.xlarge 2
r4.2xlarge 4
r4.4xlarge 8
r4.8xlarge 16
r4.16xlarge 32
r3.large	1
r3.xlarge	2
r3.2xlarge	4
r3.4xlarge	8
r3.8xlarge	16
p2.xlarge	2
p2.8xlarge	16
p2.16xlarge	32
i2.xlarge	2
i2.2xlarge	4
i2.4xlarge	8
i2.8xlarge	16
d2.xlarge	2
d2.2xlarge	4
d2.4xlarge	8
d2.8xlarge	18
'''.strip().splitlines()]

for (itype, vcpus) in VCPUS:
    print("UPDATE tpa_instancetype SET vcpus = %d WHERE name='%s';"
          % (int(vcpus), itype,))
