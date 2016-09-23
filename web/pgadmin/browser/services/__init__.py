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
from sqlalchemy.orm.loading import instances
"""Defines views for management of services"""

import json, yaml
from abc import ABCMeta, abstractmethod

import six, os, datetime
from flask import request, render_template, make_response, jsonify, current_app
from flask.ext.babel import gettext
from flask.ext.security import current_user
from pgadmin.browser import BrowserPluginModule
from pgadmin.browser.utils import NodeView
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response
from pgadmin.utils.menu import MenuItem
from pgadmin.utils import emailutil

from pgadmin.model import db, Service, MetaServerSoftware, MetaPlan, Queue


class ServiceModule(BrowserPluginModule):
    NODE_TYPE = "service"

    def get_nodes(self, *arg, **kwargs):
        metadata=[]
        for ss in MetaServerSoftware.query.order_by('id'):
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
        #TODO: (Devashish) Make all paths/filenames, patterns part of the config file
        data = request.form if request.form else json.loads(request.data.decode())
        if data[u'name'] != '':
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

                # Prepare directories
                tpa_basedir = '/opt/tpa/clusters'
                
                # TODO: (Devashish) have multiple yml files based on regions.
                tpa_conf_basedir = os.path.join(tpa_basedir, 'base_conf')
                sfx = None
                if data[u'config_type'] == 1 :
                    sfx = 'basic'
                elif data[u'config_type'] == 2 :
                    sfx = 'basic_barman'

                tpa_config_yml_base = os.path.join(tpa_conf_basedir, 'config_%s.yml' %(sfx))
                tpa_deploy_yml_base = os.path.join(tpa_conf_basedir, 'deploy.yml')

                service = None
                tpa_customerdir = None

                cluster_vars_template = None

                pgversion = None
                plan = None;

                with open(tpa_config_yml_base, 'r') as configFileBase:
                    configBase = yaml.load(configFileBase)
                    configBase['cluster_name']=data[u'name']
                    clusterTags = {}
                    clusterTags['Owner'] = current_user.id #Replace with user's name post SSO Integration
                    configBase['cluster_tags'] = clusterTags
                    instances = configBase['instances']
                    plan = MetaPlan.query.filter_by(id = data[u'plan']).first().name[4:] #Strip AWS off the plan name
                    for instance in instances:
                        instance['type'] = plan
                    configBase['instances']= instances
                    cluster_vars_template = configBase['cluster_vars']
                    del configBase['cluster_vars']

                    service = Service(
                        user_id=current_user.id,
                        name=data[u'name'],
                        server_software=data[u'server_software'],
                        plan=data[u'plan'],
                        config_type=data[u'config_type'],
                        config= json.dumps(configBase))

                    db.session.add(service)
                    db.session.flush()

                    pg2q = 'no'
                    if 4 <= service.server_software <=6:
                        pg2q = 'yes'

                    cluster_vars_template['customerId'] = current_user.id
                    cluster_vars_template['serviceId'] = service.id
                    cluster_vars_template['use_2ndquadrant_postgres'] = pg2q
                    configBase['cluster_vars'] = cluster_vars_template

                    customerdir = 'customer/%s/%s_%s' %(str(current_user.id), str(service.id), service.name)
                    tpa_customerdir = os.path.join(tpa_basedir,customerdir)
                    if not os.path.exists(tpa_customerdir):
                        os.makedirs(tpa_customerdir)

                    tpa_config_yml = os.path.join(tpa_customerdir, 'config.yml')
                    with open(tpa_config_yml, 'w') as configFile:
                        yaml.safe_dump(configBase, configFile, default_flow_style=False)
                    with open(tpa_config_yml, 'r') as configFileR:
                        configFileValidate = yaml.load(configFileR)
                        print configFileValidate['instances'][1]['volumes'][1]['device_name']


                # Create deploy.yml for service
                with open(tpa_deploy_yml_base, 'r') as deployFileBase:
                    #Prepare deploy.yml replacements
                    serverSw = MetaServerSoftware.query.filter_by(id = service.server_software).first().name
                    temp = serverSw.split();
                    tmpsize = len(temp)
                    pgversion = temp[tmpsize-1]
                    deployBase = yaml.load(deployFileBase)
                    deployBase[0]['roles'][1]['postgres_version'] = pgversion
                    #deployBase[0]['vars']['use_2ndquadrant_postgres'] = pg2q
                    #deployBase[1]['vars']['use_2ndquadrant_postgres'] = pg2q

                    tpa_deploy_yml = os.path.join(tpa_customerdir, 'deploy.yml')
                    with open(tpa_deploy_yml, 'w') as deployFile:
                        yaml.safe_dump(deployBase, deployFile, default_flow_style=False)

                # Send Email to team
                emailText = 'Team, please take care of the following request:\n User ID: %s \n Service ID: %s \n Server Software: %s \n Plan %s \n Config %s\n\nAttached are the generated yml files.\nThanks,\nTPA WebUI' %(str(current_user.id), service.id, pgversion, plan, sfx)
                emailutil.send_mail(config.PROVISIONING_REQUEST_RECIPIENTS, 'TPA Cluster Provisioning Request', emailText, [tpa_config_yml,tpa_deploy_yml])

                # Add to queue
                queue=Queue(user_id = current_user.id, service_id = service.id, service_name = service.name,queued_at = datetime.datetime.utcnow())
                db.session.add(queue)
                db.session.commit()
                #create_service_async.apply_async(args=(sg.id,))

                data[u'id'] = service.id
                data[u'name'] = service.name

                return jsonify(
                    node=self.blueprint.generate_browser_node(
                        "%d" % (service.id), None,
                        service.name,
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
        return make_json_response(status=422)
            
    # Make this a util
    def get_ansible_log_file_path_for(self, service_id):
        return '/var/log/syslog'
            
    def log_tail(self, service_id):
        # Placeholder :p. This is an incomplete implementation
        path_to_tail = '/var/log/syslog'
        log = open(path_to_tail,'r')
        if not log:
            return
        stats = os.stat(path_to_tail)
        ino = stats.st_ino
        size = stats.st_size
        if(size > 150*1024 and log.seekable() and log.seek(-150*1024, 2)):
            dummy = log

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
