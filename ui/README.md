
TPA Management Web UI and API.
==============================

## Introduction

This comprises a front-end system to allow web-based provisioning, management
and monitoring of TPA-managed database clusters.

The system is comprised of:

* A web-app that publishes a REST API to manage and query clusters and
their metrics. This is implemented with Python and the Django REST framework.

* A rich browser-based cluster management GUI that uses the above API. This is
implemented with Bootstrap, Vue.js and D3.

* Background python tasks to interface with TPA and the Graphite metrics db
populated by the 2nd Quadrant central monitoring and alerting system. This
uses Celery for task queues.

## Requirements

### External services

* TPA: From the perspective of this UI application, TPA is a provisioning
and discovery service. The web app will run TPA from a batch queue on
a non-frontline server, and the input will always be a well-formed and
validated config.yml file representing the desired cluster provisioned
state.

The syntax or format of the response message from TPA is yet to be specified.

* Target provider on which TPA managed clusters (will) reside. Currently this
is AWS only. This will be accessed both via the web app for discovery, and TPA
for management.

* Direct access to the Graphite metrics database. This implies that the metrics
update task will reside on the same system as the database.


* The 2ndQuadrant Customer Portal will be expected to authenticate users and
redirect them to tpa-ui along with authentication and session info via JWT.

### Runtime service dependencies

* PostgreSQL - app persistence.
* Celery - distributed task queue.
* Redis - persistent backend for task queue and websockets.
* UWSGI - Python WSGI container.
* Supervisor - Process management.

### Environment

* Debian stable with Python 2.x, Node.js 6.x and PostgreSQL 9.x.
* Python tools such as virtualenv and pip.

Node and npm must be installed from the nodesource distribution:
    https://github.com/nodesource/distributions#manual-installation


### Environment Variables

Python app:

* VIRTUAL_ENV=/path/to/virtualenv
* DJANGO_SETTINGS_MODULE=tpasite.conf.*
* DEBUG=(True|False)
* [dev/test only] BUILD_PATH=/path/to/build/output (default ./build)

## Directories

* __apps/__ Python (Django) app/
* __fe/__ Client browser frontend app -- HTML/CSS/JS.
* __req/__ Python requirements for app, by deployment type.
* __ansible/__ Ansible roles for deployment and dependencies.

* __[build]/static__ -- webpack will place the runtime static bundle here.
* __[build]/node_modules__ -- npm will use this as its "global"
installation prefix.

## Development Quickstart

By default, the system will be configured with dev settings. This can
be changed by setting the DJANGO_SETTINGS_MODULE to one of the other
role configs in tpasite.conf.

* Create a virtualenv for the project and activate it.

* Setup the environment and run the internal dev server on port 8000:

[ TODO -- Add instructions about the Makefile, npm and webpack. ]

```
~/tpa/ui > . ./initenv.sh
...
~/tpa/ui > make dev-setup
...
~/tpa/ui > npm install
...
~/tpa/ui > pip install -r req/dev.txt
...
~/tpa/ui > createdb tpa-dev   # DB suffix matches profile
...
~/tpa/ui > ./apps/manage.py migrate
...
~/tpa/ui > webpack -hw &
...
~/tpa/ui > ./apps/manage.py runserver
```

## Authentication and Authorization

The app uses JWT for authenticating users. There is an n-to-n relationship
between Users and Tenants, where Tenant represents and organization
or institution which owns clusters and deputes users to manage them on
its behalf. Access to view and edit tenant-owned resources by users is
implemented using django-guardian for RBAC.

## YAML tags

__TODO__ - Audit and ensure we support all in ui/db/yaml.

```
LATER

cluster_rules
    from_port
    to_port
    proto

cluster_vars
customerId

co_list
dn_list
dn_replica_list

log
node
os
spot_launch_group
spot_price
spot_wait_timeout
termination_protection

PGLOGICAL

tags:
    group
    has_tct

Done:

x Name
x Owner
x assign_eip
x az
x backup
x cidr
x cidr_ip
x cluster_name
x cluster_network
x cluster_tags
x ec2_ami
x ec2_ami_user
x ec2_vpc
x ec2_vpc_subnets
x ephemeral
x image
x instances
x role
x region
x type
x subnet
x tags
x upstream

x volumes
x     volume_size
x     volume_type
x     delete_on_termination
x     device_name


```
