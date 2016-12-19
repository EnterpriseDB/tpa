
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

Note that this means you have to run npm with the -g option set, and
ensure you source ./initenv.sh before running npm.

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

~/tpa/ui > pip install -r req/dev.txt
...
~/tpa/ui > createdb tpa-dev
...
~/tpa/ui > ./apps/manage.py migrate
...
~/tpa/ui > webpack -hw &
...
~/tpa/ui > ./apps/manage.py runserver
```


## YAML tags

__TODO__ - Audit and ensure we support all in ui/db/yaml.

```
cluster_rules
cluster_vars
co_list
customerId
delete_on_termination
device_name
dn_list
dn_replica_list
ephemeral
from_port
group
has_tct
log
node
os
proto
x region
spot_launch_group
spot_price
spot_wait_timeout
termination_protection
to_port
x type
volume_size
volume_type
volumes

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
x image
x instances
x role
x subnet
x tags
x upstream
```
