##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Defines views for management of Fts Configuration node"""

import json
from functools import wraps

import pgadmin.browser.services.server_groups.servers.databases as databases
from flask import render_template, make_response, current_app, request, jsonify
from flask.ext.babel import gettext as _
from pgadmin.browser.services.server_groups.servers.databases.schemas.utils \
    import SchemaChildModule
from pgadmin.browser.utils import PGChildNodeView
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response, internal_server_error, gone
from pgadmin.utils.ajax import precondition_required
from pgadmin.utils.driver import get_driver

from config import PG_DEFAULT_DRIVER


class FtsConfigurationModule(SchemaChildModule):
    """
     class FtsConfigurationModule(SchemaChildModule)

        A module class for FTS Configuration node derived from SchemaChildModule.

    Methods:
    -------
    * __init__(*args, **kwargs)
      - Method is used to initialize the FtsConfigurationModule and
        it's base module.

    * get_nodes(gid, sid, did, scid)
      - Method is used to generate the browser collection node.

    * node_inode()
      - Method is overridden from its base class to make the node as leaf node

    * script_load()
      - Load the module script for FTS Configuration, when any of the schema
      node is initialized.

    """
    NODE_TYPE = 'fts_configuration'
    COLLECTION_LABEL = _('FTS Configurations')

    def __init__(self, *args, **kwargs):
        self.min_ver = None
        self.max_ver = None
        self.manager = None
        super(FtsConfigurationModule, self).__init__(*args, **kwargs)

    def get_nodes(self, gid, sid, did, scid):
        """
        Generate the collection node
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        """
        yield self.generate_browser_collection_node(scid)

    @property
    def node_inode(self):
        """
        Override the property to make the node as leaf node
        """
        return False

    @property
    def script_load(self):
        """
        Load the module script for fts template, when any of the schema
        node is initialized.
        """
        return databases.DatabaseModule.NODE_TYPE


blueprint = FtsConfigurationModule(__name__)


class FtsConfigurationView(PGChildNodeView):
    """
    class FtsConfigurationView(PGChildNodeView)

        A view class for FTS Configuration node derived from PGChildNodeView.
        This class is responsible for all the stuff related to view like
        create/update/delete FTS Configuration,
        showing properties of node, showing sql in sql pane.

    Methods:
    -------
    * __init__(**kwargs)
      - Method is used to initialize the FtsConfigurationView and it's base view.

    * module_js()
      - This property defines (if javascript) exists for this node.
        Override this property for your own logic

    * check_precondition()
      - This function will behave as a decorator which will checks
        database connection before running view, it will also attaches
        manager,conn & template_path properties to self

    * list()
      - This function is used to list all the  nodes within that collection.

    * nodes()
      - This function will be used to create all the child node within collection.
        Here it will create all the FTS Configuration nodes.

    * node()
      - This function will be used to create a node given its oid
        Here it will create the FTS Template node based on its oid

    * properties(gid, sid, did, scid, cfgid)
      - This function will show the properties of the selected FTS Configuration node

    * create(gid, sid, did, scid)
      - This function will create the new FTS Configuration object

    * update(gid, sid, did, scid, cfgid)
      - This function will update the data for the selected FTS Configuration node

    * delete(self, gid, sid, did, scid, cfgid):
      - This function will drop the FTS Configuration object

    * msql(gid, sid, did, scid, cfgid)
      - This function is used to return modified SQL for the selected node

    * get_sql(data, cfgid)
      - This function will generate sql from model data

    * sql(gid, sid, did, scid, cfgid):
      - This function will generate sql to show in sql pane for node.

    * parsers(gid, sid, did, scid):
      - This function will fetch all ftp parsers from the same schema

    * copyConfig():
      - This function will fetch all existed fts configurations from same schema

    * tokens():
      - This function will fetch all tokens from fts parser related to node

    * dictionaries():
      - This function will fetch all dictionaries related to node

    * dependents(gid, sid, did, scid, cfgid):
      - This function get the dependents and return ajax response for the node.

    * dependencies(self, gid, sid, did, scid, cfgid):
      - This function get the dependencies and return ajax response for node.

    """

    node_type = blueprint.node_type

    parent_ids = [
        {'type': 'int', 'id': 'gid'},
        {'type': 'int', 'id': 'sid'},
        {'type': 'int', 'id': 'did'},
        {'type': 'int', 'id': 'scid'}
    ]
    ids = [
        {'type': 'int', 'id': 'cfgid'}
    ]

    operations = dict({
        'obj': [
            {'get': 'properties', 'delete': 'delete', 'put': 'update'},
            {'get': 'list', 'post': 'create'}
        ],
        'children': [{
            'get': 'children'
        }],
        'delete': [{'delete': 'delete'}],
        'nodes': [{'get': 'node'}, {'get': 'nodes'}],
        'sql': [{'get': 'sql'}],
        'msql': [{'get': 'msql'}, {'get': 'msql'}],
        'stats': [{'get': 'statistics'}],
        'dependency': [{'get': 'dependencies'}],
        'dependent': [{'get': 'dependents'}],
        'module.js': [{}, {}, {'get': 'module_js'}],
        'parsers': [{'get': 'parsers'},
                    {'get': 'parsers'}],
        'copyConfig': [{'get': 'copyConfig'},
                       {'get': 'copyConfig'}],
        'tokens': [{'get': 'tokens'}, {'get': 'tokens'}],
        'dictionaries': [{}, {'get': 'dictionaries'}],
    })

    def _init_(self, **kwargs):
        self.conn = None
        self.template_path = None
        self.manager = None
        super(FtsConfigurationView, self).__init__(**kwargs)

    def module_js(self):
        """
        Load JS file (fts_configuration.js) for this module.
        """
        return make_response(
            render_template(
                "fts_configuration/js/fts_configuration.js",
                _=_
            ),
            200, {'Content-Type': 'application/x-javascript'}
        )

    def check_precondition(f):
        """
        This function will behave as a decorator which will checks
        database connection before running view, it will also attaches
        manager,conn & template_path properties to self
        """

        @wraps(f)
        def wrap(*args, **kwargs):
            # Here args[0] will hold self & kwargs will hold gid,sid,did
            self = args[0]
            self.manager = get_driver(PG_DEFAULT_DRIVER).connection_manager(
                kwargs['sid'])
            self.conn = self.manager.connection(did=kwargs['did'])
            # If DB not connected then return error to browser
            if not self.conn.connected():
                return precondition_required(
                    _("Connection to the server has been lost!")
                )
            # we will set template path for sql scripts depending upon server version
            ver = self.manager.version
            if ver >= 90100:
                self.template_path = 'fts_configuration/sql/9.1_plus'
            return f(*args, **kwargs)

        return wrap

    @check_precondition
    def list(self, gid, sid, did, scid):
        """
        List all FTS Configuration nodes.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
        """

        sql = render_template(
            "/".join([self.template_path, 'properties.sql']),
            scid=scid
        )
        status, res = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=res)

        return ajax_response(
            response=res['rows'],
            status=200
        )

    @check_precondition
    def nodes(self, gid, sid, did, scid):
        """
        Return all FTS Configurations to generate nodes.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
        """

        res = []
        sql = render_template(
            "/".join([self.template_path, 'nodes.sql']),
            scid=scid
        )
        status, rset = self.conn.execute_2darray(sql)
        if not status:
            return internal_server_error(errormsg=rset)

        for row in rset['rows']:
            res.append(
                self.blueprint.generate_browser_node(
                    row['oid'],
                    did,
                    row['name'],
                    icon="icon-fts_configuration"
                ))

        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def node(self, gid, sid, did, scid, cfgid):
        """
        Return FTS Configuration node to generate node

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            cfgid: fts Configuration id
        """

        sql = render_template(
            "/".join([self.template_path, 'nodes.sql']),
            cfgid=cfgid
        )
        status, rset = self.conn.execute_2darray(sql)
        if not status:
            return internal_server_error(errormsg=rset)

        if len(rset['rows']) == 0:
            return gone(_("""
                Could not find the FTS Configuration node.
                """))

        for row in rset['rows']:
            return make_json_response(
                data=self.blueprint.generate_browser_node(
                    row['oid'],
                    did,
                    row['name'],
                    icon="icon-fts_configuration"
                ),
                status=200
            )

    @check_precondition
    def properties(self, gid, sid, did, scid, cfgid):
        """
        Show properties of FTS Configuration node

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            cfgid: fts Configuration id
        """

        sql = render_template(
            "/".join([self.template_path, 'properties.sql']),
            scid=scid,
            cfgid=cfgid
        )
        status, res = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=res)

        if len(res['rows']) == 0:
            return gone(_("""
                Could not find the FTS Configuration node.
                """))

        # In edit mode fetch token/dictionary list also
        if cfgid:
            sql = render_template("/".join([self.template_path,
                                            'tokenDictList.sql']),
                                  cfgid=cfgid)

            status, rset = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=rset)

            res['rows'][0]['tokens'] = rset['rows']

        return ajax_response(
            response=res['rows'][0],
            status=200
        )

    @check_precondition
    def create(self, gid, sid, did, scid):
        """
        This function will creates new the FTS Configuration object
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        """

        # Mandatory fields to create a new FTS Configuration
        required_args = [
            'schema',
            'name'
        ]

        data = request.form if request.form else json.loads(
            request.data.decode())
        for arg in required_args:
            if arg not in data:
                return make_json_response(
                    status=410,
                    success=0,
                    errormsg=_(
                        "Couldn't find the required parameter (%s)." % arg
                    )
                )

        # Either copy config or parser must be present in data
        if 'copy_config' not in data and 'prsname' not in data:
            return make_json_response(
                status=410,
                success=0,
                errormsg=_(
                    "provide atleast copy config or parser"
                )
            )

        try:
            # Fetch schema name from schema oid
            sql = render_template("/".join([self.template_path,
                                            'schema.sql']),
                                  data=data,
                                  conn=self.conn,
                                  )

            status, schema = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(errormsg=schema)

            # Replace schema oid with schema name before passing to create.sql
            # To generate proper sql query
            new_data = data.copy()
            new_data['schema'] = schema

            sql = render_template(
                "/".join([self.template_path, 'create.sql']),
                data=new_data,
                conn=self.conn,
            )
            status, res = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(errormsg=res)

            # We need cfgid to add object in tree at browser,
            # Below sql will give the same
            sql = render_template(
                "/".join([self.template_path, 'properties.sql']),
                name=data['name']
            )
            status, cfgid = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(errormsg=cfgid)

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    cfgid,
                    did,
                    data['name'],
                    icon="icon-fts_configuration"
                )
            )
        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def update(self, gid, sid, did, scid, cfgid):
        """
        This function will update FTS Configuration node
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: fts Configuration id
        """
        data = request.form if request.form else json.loads(
            request.data.decode())

        # Fetch sql query to update fts Configuration
        sql = self.get_sql(gid, sid, did, scid, data, cfgid)
        try:
            if sql and sql.strip('\n') and sql.strip(' '):
                status, res = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                if cfgid is not None:
                    sql = render_template(
                        "/".join([self.template_path, 'nodes.sql']),
                        cfgid=cfgid,
                        scid=scid
                    )

                status, res = self.conn.execute_dict(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                if len(res['rows']) == 0:
                    return gone(_("""
                        Could not find the FTS Configuration node to update.
                    """))

                data = res['rows'][0]
                return make_json_response(
                    success=1,
                    info="FTS Configuration Updated.",
                    data={
                        'id': cfgid,
                        'sid': sid,
                        'gid': gid,
                        'did': did,
                        'scid': scid
                    }
                )
            # In case FTS Configuration node is not present
            else:
                return make_json_response(
                    success=1,
                    info="Nothing to update",
                    data={
                        'id': cfgid,
                        'sid': sid,
                        'gid': gid,
                        'did': did,
                        'scid': scid
                    }
                )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def delete(self, gid, sid, did, scid, cfgid):
        """
        This function will drop the FTS Configuration object
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: FTS Configuration id
        """
        # Below will decide if it's simple drop or drop with cascade call
        if self.cmd == 'delete':
            # This is a cascade operation
            cascade = True
        else:
            cascade = False

        try:
            # Get name for FTS Configuration from cfgid
            sql = render_template(
                "/".join([self.template_path, 'get_name.sql']),
                cfgid=cfgid
            )
            status, res = self.conn.execute_dict(sql)
            if not status:
                return internal_server_error(errormsg=res)

            if len(res['rows']) == 0:
                return gone(_("""
                        Could not find the FTS Configuration node to delete.
                    """))

            # Drop FTS Configuration
            result = res['rows'][0]
            sql = render_template(
                "/".join([self.template_path, 'delete.sql']),
                name=result['name'],
                schema=result['schema'],
                cascade=cascade
            )

            status, res = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(errormsg=res)

            return make_json_response(
                success=1,
                info=_("FTS Configuration dropped"),
                data={
                    'id': cfgid,
                    'sid': sid,
                    'gid': gid,
                    'did': did,
                    'scid': scid
                }
            )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def msql(self, gid, sid, did, scid, cfgid=None):
        """
        This function returns modified SQL
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: FTS Configuration id
        """
        data = {}
        for k, v in request.args.items():
            try:
                data[k] = json.loads(v)
            except ValueError:
                data[k] = v

        # Fetch sql query for modified data
        sql = self.get_sql(gid, sid, did, scid, data, cfgid)

        if isinstance(sql, str) and sql and sql.strip('\n') and sql.strip(' '):
            return make_json_response(
                data=sql,
                status=200
            )
        else:
            return make_json_response(
                data="--modified SQL",
                status=200
            )

    def get_sql(self, gid, sid, did, scid, data, cfgid=None):
        """
        This function will return SQL for model data
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: fts Configuration id
        """
        try:
            # Fetch sql for update
            if cfgid is not None:
                sql = render_template(
                    "/".join([self.template_path, 'properties.sql']),
                    cfgid=cfgid,
                    scid=scid
                )

                status, res = self.conn.execute_dict(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                if len(res['rows']) == 0:
                    return gone(_("""
                        Could not find the FTS Configuration node.
                    """))

                old_data = res['rows'][0]

                # If user has changed the schema then fetch new schema directly
                # using its oid otherwise fetch old schema name using its oid
                sql = render_template(
                    "/".join([self.template_path, 'schema.sql']),
                    data=data)

                status, new_schema = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=new_schema)

                # Replace schema oid with schema name
                new_data = data.copy()
                if 'schema' in new_data:
                    new_data['schema'] = new_schema

                # Fetch old schema name using old schema oid
                sql = render_template(
                    "/".join([self.template_path, 'schema.sql']),
                    data=old_data
                )

                status, old_schema = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=old_schema)

                # Replace old schema oid with old schema name
                old_data['schema'] = old_schema

                sql = render_template(
                    "/".join([self.template_path, 'update.sql']),
                    data=new_data, o_data=old_data
                )
                # Fetch sql query for modified data
            else:
                # Fetch schema name from schema oid
                sql = render_template(
                    "/".join([self.template_path, 'schema.sql']),
                    data=data
                )

                status, schema = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=schema)

                # Replace schema oid with schema name
                new_data = data.copy()
                new_data['schema'] = schema

                if 'name' in new_data and \
                                'schema' in new_data:
                    sql = render_template("/".join([self.template_path,
                                                    'create.sql']),
                                          data=new_data,
                                          conn=self.conn
                                          )
                else:
                    sql = "-- incomplete definition"
            return str(sql.strip('\n'))

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def parsers(self, gid, sid, did, scid):
        """
        This function will return fts parsers list for FTS Configuration
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        """
        # Fetch last system oid
        datlastsysoid = self.manager.db_info[did]['datlastsysoid']

        sql = render_template(
            "/".join([self.template_path, 'parser.sql']),
            parser=True
        )
        status, rset = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=rset)

        # Empty set is added before actual list as initially it will be visible
        # at parser control while creating a new FTS Configuration
        res = [{'label': '', 'value': ''}]
        for row in rset['rows']:
            if row['schemaoid'] > datlastsysoid:
                row['prsname'] = row['nspname'] + '.' + row['prsname']

            res.append({'label': row['prsname'],
                        'value': row['prsname']})
        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def copyConfig(self, gid, sid, did, scid):
        """
        This function will return copy config list for FTS Configuration
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        """
        # Fetch last system oid
        datlastsysoid = self.manager.db_info[did]['datlastsysoid']

        sql = render_template(
            "/".join([self.template_path, 'copy_config.sql']),
            copy_config=True
        )
        status, rset = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=rset)

        # Empty set is added before actual list as initially it will be visible
        # at copy_config control while creating a new FTS Configuration
        res = [{'label': '', 'value': ''}]
        for row in rset['rows']:
            if row['oid'] > datlastsysoid:
                row['cfgname'] = row['nspname'] + '.' + row['cfgname']

            res.append({'label': row['cfgname'],
                        'value': row['cfgname']})
        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def tokens(self, gid, sid, did, scid, cfgid=None):
        """
        This function will return token list of fts parser node related to
        current FTS Configuration node
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: fts configuration id
        """
        try:
            res = []
            if cfgid is not None:
                sql = render_template(
                    "/".join([self.template_path, 'parser.sql']),
                    cfgid=cfgid
                )
                status, parseroid = self.conn.execute_scalar(sql)

                if not status:
                    return internal_server_error(errormsg=parseroid)

                sql = render_template(
                    "/".join([self.template_path, 'tokens.sql']),
                    parseroid=parseroid
                )
                status, rset = self.conn.execute_dict(sql)

                for row in rset['rows']:
                    res.append({'label': row['alias'],
                                'value': row['alias']})

            return make_json_response(
                data=res,
                status=200
            )

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def dictionaries(self, gid, sid, did, scid, cfgid=None):
        """
        This function will return dictionary list for FTS Configuration
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        """
        sql = render_template(
            "/".join([self.template_path, 'dictionaries.sql'])
        )
        status, rset = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=rset)

        res = []
        for row in rset['rows']:
            res.append({'label': row['dictname'],
                        'value': row['dictname']})
        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def sql(self, gid, sid, did, scid, cfgid):
        """
        This function will reverse generate sql for sql panel
        :param gid: group id
        :param sid: server id
        :param did: database id
        :param scid: schema id
        :param cfgid: FTS Configuration id
        """
        try:
            sql = render_template(
                "/".join([self.template_path, 'sql.sql']),
                cfgid=cfgid,
                scid=scid,
                conn=self.conn
            )
            status, res = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(
                    _(
                        "ERROR: Couldn't generate reversed engineered query for the FTS Configuration!\n{0}"
                    ).format(
                        res
                    )
                )

            if res is None:
                return gone(
                    _(
                        "ERROR: Couldn't generate reversed engineered query for FTS Configuration node!")
                )

            return ajax_response(response=res)

        except Exception as e:
            current_app.logger.exception(e)
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def dependents(self, gid, sid, did, scid, cfgid):
        """
        This function get the dependents and return ajax response
        for the FTS Configuration node.

        Args:
            gid: Server Group ID
            sid: Server ID
            did: Database ID
            scid: Schema ID
            cfgid: FTS Configuration ID
        """
        dependents_result = self.get_dependents(self.conn, cfgid)
        return ajax_response(
            response=dependents_result,
            status=200
        )

    @check_precondition
    def dependencies(self, gid, sid, did, scid, cfgid):
        """
        This function get the dependencies and return ajax response
        for the FTS Configuration node.

        Args:
            gid: Server Group ID
            sid: Server ID
            did: Database ID
            scid: Schema ID
            cfgid: FTS Configuration ID
        """
        dependencies_result = self.get_dependencies(self.conn, cfgid)
        return ajax_response(
            response=dependencies_result,
            status=200
        )


FtsConfigurationView.register_node_view(blueprint)
