##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################
"""Defines views for management of clusters"""

import json
from abc import ABCMeta, abstractmethod

import six
import pgadmin.browser.services as ss
from flask import request, render_template, make_response, jsonify
from flask.ext.babel import gettext
from flask.ext.security import current_user
from pgadmin.browser import BrowserPluginModule
from pgadmin.browser.utils import NodeView
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response
from pgadmin.utils.menu import MenuItem

from pgadmin.model import db, Service, MetaServerSoftware


class ClusterModule(ss.ServicePluginModule):
    NODE_TYPE = "cluster"

    def get_nodes(self,service_id):
        print "Getting clusters for service "+str(service_id)
        """Return a JSON document listing the clusters for the user"""
        services = Service.query.filter_by(
            user_id=current_user.id, id=service_id
        ).order_by("id")
        for idx, service in enumerate(services):
            clusters = json.loads(service.config)['clusters']
            for cluster in clusters :
                print cluster
                yield self.generate_browser_node(
                    "%d" % (cluster['cluster_id']), service_id,
                    cluster['cluster_name'],
                    "icon-%s" % self.node_type,
                    True,
                    self.node_type,
                    can_delete=False
                )
            

    @property
    def node_type(self):
        """
        node_type
        Node type for Cluster is cluster. It is defined by NODE_TYPE
        static attribute of the class.
        """
        return self.NODE_TYPE

    @property
    def script_load(self):
        """
        script_load
        Load the cluster javascript module on loading of browser module.
        """
        return ss.ServiceModule.NODE_TYPE

    def register_preferences(self):
        """
        register_preferences
        Overrides the register_preferences PgAdminModule, because - we will not
        register any preference for cluster (specially the show_node
        preference.)
        """
        pass


class ClusterMenuItem(MenuItem):
    def __init__(self, **kwargs):
        kwargs.setdefault("type", ClusterModule.NODE_TYPE)
        super(ClusterMenuItem, self).__init__(**kwargs)


@six.add_metaclass(ABCMeta)
class ClusterPluginModule(BrowserPluginModule):
    """
    Base class for cluster plugins.
    """

    @abstractmethod
    def get_nodes(self, *arg, **kwargs):
        pass


blueprint = ClusterModule(__name__, static_url_path='')
    
class ClusterView(NodeView):
    metadata = []
    node_type = ClusterModule.NODE_TYPE
    parent_ids = [{'type': 'int', 'id': 'service_id'}]
    ids = [{'type': 'int', 'id': 'cluster_id'}]

    def list(self):
        res = []
        for sg in Cluster.query.filter_by(
                user_id=current_user.id
        ).order_by('name'):
            res.append({
                'id': sg.id,
                'name': sg.name
            })

        return ajax_response(response=res, status=200)
            

    def delete(self, cluster_id):
        """Delete a cluster node in the settings database"""

        groups = Cluster.query.filter_by(
            user_id=current_user.id
        ).order_by("id")

        # if cluster id is 1 we won't delete it.
        sg = groups.first()

        if sg.id == cluster_id:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified cluster cannot be deleted.'
                )
            )

        # There can be only one record at most
        sg = groups.filter_by(id=cluster_id).first()

        if sg is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified cluster could not be found.'
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

    def update(self, cluster_id):
        """Update the cluster properties"""

        # There can be only one record at most
        cluster = Cluster.query.filter_by(
            user_id=current_user.id,
            id=cluster_id).first()

        data = request.form if request.form else json.loads(request.data.decode())

        if cluster is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified cluster could not be found.'
                )
            )
        else:
            try:
                if u'name' in data:
                    cluster.name = data[u'name']
                db.session.commit()
            except Exception as e:
                return make_json_response(
                    status=410, success=0, errormsg=e.message
                )

        return make_json_response(result=request.form)

    def properties(self, service_id,cluster_id):
        """Update the cluster properties"""
        services = Service.query.filter_by(
            user_id=current_user.id, id=service_id
        ).order_by("id")
        for idx, service in enumerate(services):
            clusters = json.loads(service.config)['clusters']
            i=0
            for cluster in clusters :
                if cluster['cluster_id'] == cluster_id:
                    i+=1
                    return ajax_response(
                        response={'id': cluster_id, 'name': cluster['cluster_name'], 'tags':cluster['cluster_tags']},
                        status=200
                    )
                    
                    

        # There can be only one record at most
        sg = Cluster.query.filter_by(
            user_id=current_user.id,
            id=cluster_id).first()

        if sg is None:
            return make_json_response(
                status=417,
                success=0,
                errormsg=gettext(
                    'The specified cluster could not be found.'
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
                check_sg = Cluster.query.filter_by(
                    user_id=current_user.id,
                    name=data[u'name']).first()

                # Throw error if cluster already exists...
                if check_sg is not None:
                    return make_json_response(
                        status=409,
                        success=0,
                        errormsg=gettext('Cluster already exists')
                    )
                jsonIn = open('/home/devashish/2q/sources/workspace/pgadmin4/web/pgadmin/browser/clusters/static/json/config_basic.json')
                conf = json.load(jsonIn)
                sg = Cluster(
                    user_id=current_user.id,
                    name=data[u'name'],
                    server_software=data[u'server_software'],
                    plan=data[u'plan'],
                    config_type=data[u'config_type'],
                    config= json.dumps(conf))
                db.session.add(sg)
                db.session.commit()
                
                data[u'id'] = sg.id
                data[u'name'] = sg.name

                return jsonify(
                    node=self.blueprint.generate_browser_node(
                        "%d" % (sg.id), None,
                        sg.name,
                        "icon-%s" % self.node_type,
                        True,
                        self.node_type,
                        can_delete=True  # This is user created hence can deleted
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
                errormsg=gettext('No cluster name was specified'))

    def sql(self, cluster_id):
        return make_json_response(status=422)

    def modified_sql(self, cluster_id):
        return make_json_response(status=422)

    def statistics(self, cluster_id):
        return make_json_response(status=422)

    def dependencies(self, cluster_id):
        return make_json_response(status=422)

    def dependents(self, cluster_id):
        return make_json_response(status=422)

    def module_js(self, **kwargs):
        """
        This property defines (if javascript) exists for this node.
        Override this property for your own logic.
        """
        return make_response(
            render_template("clusters/clusters.js"),
            200, {'Content-Type': 'application/x-javascript'}
        )

    def nodes(self, cluster_id=None):
        """Return a JSON document listing the clusters for the user"""
        nodes = []

        if cluster_id is None:
            groups = Cluster.query.filter_by(user_id=current_user.id)
        else:
            groups = Cluster.query.filter_by(user_id=current_user.id,
                                                 id=cluster_id).first()

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

    def node(self, cluster_id):
        return self.nodes(cluster_id)


ClusterView.register_node_view(blueprint)
