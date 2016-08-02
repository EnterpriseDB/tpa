##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################
import pgadmin
import config
"""Defines views for management of services"""

import json
from abc import ABCMeta, abstractmethod
from celery import Celery

import six, os
from flask import request, render_template, make_response, jsonify, current_app
from flask.ext.babel import gettext
from flask.ext.security import current_user
from pgadmin import celery
from pgadmin.browser import BrowserPluginModule
from pgadmin.browser.utils import NodeView
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response
from pgadmin.utils.menu import MenuItem
from pgadmin.tasks import create_service_async

from pgadmin.model import db, Service, MetaServerSoftware


class ServiceModule(BrowserPluginModule):
    NODE_TYPE = "service"

    def get_nodes(self, *arg, **kwargs):
        print "Broker "+str(current_app.config['CELERY_BROKER_URL'])
        metadata=[]
        print "Fetching nodes"
        for ss in MetaServerSoftware.query.order_by('id'):
            print("Server soft" +ss.name)
            metadata.append({
                'id': ss.id,
                'name': ss.name
            })
        """Return a JSON document listing the services for the user"""
        services = Service.query.filter_by(
            user_id=current_user.id
        ).order_by("id")
        for idx, service in enumerate(services):
            yield self.generate_browser_node(
                "%d" % (service.id), None,
                service.name,
                "icon-%s" % self.node_type,
                True,
                self.node_type,
                can_delete=True if idx > 0 else False
            )
            #print json.loads(service.config)['instances'][0]['name']

    @property
    def node_type(self):
        """
        node_type
        Node type for Service is service. It is defined by NODE_TYPE
        static attribute of the class.
        """
        return self.NODE_TYPE

    @property
    def script_load(self):
        """
        script_load
        Load the service javascript module on loading of browser module.
        """
        return None

    def register_preferences(self):
        """
        register_preferences
        Overrides the register_preferences PgAdminModule, because - we will not
        register any preference for service (specially the show_node
        preference.)
        """
        pass


class ServiceMenuItem(MenuItem):
    def __init__(self, **kwargs):
        kwargs.setdefault("type", ServiceModule.NODE_TYPE)
        super(ServiceMenuItem, self).__init__(**kwargs)


@six.add_metaclass(ABCMeta)
class ServicePluginModule(BrowserPluginModule):
    """
    Base class for service plugins.
    """

    @abstractmethod
    def get_nodes(self, *arg, **kwargs):
        pass


blueprint = ServiceModule(__name__, static_url_path='')
    
class ServiceView(NodeView):
    metadata = []
    node_type = ServiceModule.NODE_TYPE
    parent_ids = []
    ids = [{'type': 'int', 'id': 'service_id'}]

    def list(self):
        res = []
        for sg in Service.query.filter_by(
                user_id=current_user.id
        ).order_by('name'):
            res.append({
                'id': sg.id,
                'name': sg.name
            })

        return ajax_response(response=res, status=200)
            

    def delete(self, service_id):
        """Delete a service node in the settings database"""

        groups = Service.query.filter_by(
            user_id=current_user.id
        ).order_by("id")

        # if service id is 1 we won't delete it.
        sg = groups.first()

        if sg.id == service_id:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified service cannot be deleted.'
                )
            )

        # There can be only one record at most
        sg = groups.filter_by(id=service_id).first()

        if sg is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified service could not be found.'
                )
            )
        else:
            try:
                db.session.delete(sg)
                db.session.commit()
            except Exception as e:
                return make_json_response(
                    status=410, success=0, errormsg=e.message
                )

        return make_json_response(result=request.form)

    def update(self, service_id):
        """Update the service properties"""

        # There can be only one record at most
        service = Service.query.filter_by(
            user_id=current_user.id,
            id=service_id).first()

        data = request.form if request.form else json.loads(request.data.decode())

        if service is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified service could not be found.'
                )
            )
        else:
            try:
                if u'name' in data:
                    service.name = data[u'name']
                db.session.commit()
            except Exception as e:
                return make_json_response(
                    status=410, success=0, errormsg=e.message
                )

        return make_json_response(result=request.form)

    def properties(self, service_id):
        """Update the service properties"""

        # There can be only one record at most
        sg = Service.query.filter_by(
            user_id=current_user.id,
            id=service_id).first()

        if sg is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified service could not be found.'
                )
            )
        else:
            return ajax_response(
                response={'id': sg.id, 'name': sg.name, 'server_software': sg.server_software, 'plan':sg.plan, 'config':sg.config},
                status=200
            )
            
 
    def create(self):
        data = request.form if request.form else json.loads(request.data.decode())
        if data[u'name'] != '':
            print data
            try:
                check_sg = Service.query.filter_by(
                    user_id=current_user.id,
                    name=data[u'name']).first()

                # Throw error if service already exists...
                if check_sg is not None:
                    return make_json_response(
                        status=409,
                        success=0,
                        errormsg=gettext('Service already exists')
                    )
                jsonIn = open('/home/devashish/2q/sources/workspace/pgadmin4/web/pgadmin/browser/services/static/json/config_basic.json')
                conf = json.load(jsonIn)
                sg = Service(
                    user_id=current_user.id,
                    name=data[u'name'],
                    server_software=data[u'server_software'],
                    plan=data[u'plan'],
                    config_type=data[u'config_type'],
                    config= json.dumps(conf))
                
                db.session.add(sg)
                db.session.commit()
                
                print "SG Id is "+str(sg.id)
                create_service_async.apply_async(args=(sg.id,))
                
                
                data[u'id'] = sg.id
                data[u'name'] = sg.name

                return jsonify(
                    node=self.blueprint.generate_browser_node(
                        "%d" % (sg.id), None,
                        sg.name,
                        "icon-%s" % self.node_type,
                        True,
                        self.node_type,
                        can_delete=True  # This is user created hence can be deleted
                    )
                )
            except Exception as e:
                return make_json_response(
                    status=410,
                    success=0,
                    errormsg=e.message)

        else:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext('No service name was specified'))
            
    def status(self,service_id):
        print "IN status method of Service %d" %(service_id)
        return make_json_response(status=422)
            
    # Make this a util
    def get_ansible_log_file_path_for(self, service_id):
        return '/var/log/syslog'
            
    def log_tail(self, service_id):
        path_to_tail = '/var/log/syslog'
        log = open(path_to_tail,'r')
        if not log:
            return
        stats = os.stat(path_to_tail)
        ino = stats.st_ino
        size = stats.st_size
        if(size > 150*1024 and log.seekable() and log.seek(-150*1024, 2)):
            dummy = log
        
        
        
    def get_ansible_log_file_path_for(self, service_id):
        return '/var/log/syslog'
        

    def sql(self, service_id):
        return make_json_response(status=422)

    def modified_sql(self, service_id):
        return make_json_response(status=422)

    def statistics(self, service_id):
        return make_json_response(status=422)

    def dependencies(self, service_id):
        return make_json_response(status=422)

    def dependents(self, service_id):
        return make_json_response(status=422)

    def module_js(self, **kwargs):
        """
        This property defines (if javascript) exists for this node.
        Override this property for your own logic.
        """
        return make_response(
            render_template("services/services.js"),
            200, {'Content-Type': 'application/x-javascript'}
        )

    def nodes(self, service_id=None):
        """Return a JSON document listing the services for the user"""
        nodes = []

        if service_id is None:
            groups = Service.query.filter_by(user_id=current_user.id)
        else:
            groups = Service.query.filter_by(user_id=current_user.id,
                                                 id=service_id).first()

        for group in groups:
            print group.name
            nodes.append(
                self.blueprint.generate_browser_node(
                    "%d" % (group.id), None,
                    group.name,
                    "icon-%s" % self.node_type,
                    True,
                    self.node_type
                )
            )

        return make_json_response(data=nodes)

    def node(self, service_id):
        return self.nodes(service_id)
        
    


ServiceView.register_node_view(blueprint)
