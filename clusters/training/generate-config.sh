#!/bin/bash

issue=${1:?Redmine issue not specified}
hosts=${2:?Number of VMs not specified}
names=$(wc -l hostnames.txt|awk '{print $1}')

if [ $hosts -gt $names ];
then
    echo "Please add more hostnames to hostnames.txt"
    exit
fi

cat <<PREAMBLE
---

cluster_name: training_$issue
cluster_tags:
  Owner: Training
  Reference: https://redmine.2ndquadrant.it/issues/$issue

cluster_vars:
  cluster_network: 10.33.115.0/24

cluster_rules:
  - {proto: tcp, from_port: 0, to_port: 65535, cidr_ip: 0.0.0.0/0}

ec2_ami:
  Name: debian-jessie-amd64-hvm-2017-01-15-1221-ebs
ec2_ami_user: admin

ec2_vpc:
  Name: Test

instances:
PREAMBLE

i=0
for name in $(sort --random-sort hostnames.txt|head -$hosts);
do
    i=$((i+1))
cat <<INSTANCE
  - node: $i
    Name: $name
    type: t2.micro
    region: eu-west-1
    subnet: 10.33.115.0/24
    role:
      - primary
INSTANCE
done
