
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


## Directories

* __apps/__ Python (Django) app/
* __fe/__ Client browser frontend app -- HTML/CSS/JS.
* __req/__ Python requirements for app, by deployment type.
* __ansible/__ Ansible roles for deployment and dependencies.
