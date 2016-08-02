##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Implements Exclusion constraint Node"""

import json
from functools import wraps

import pgadmin.browser.services.server_groups.servers.databases as database
from flask import render_template, make_response, request, jsonify
from flask.ext.babel import gettext as _
from pgadmin.browser.services.server_groups.servers.databases.schemas.tables.constraints.type \
    import ConstraintRegistry, ConstraintTypeModule
from pgadmin.browser.utils import PGChildNodeView
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response, internal_server_error
from pgadmin.utils.ajax import precondition_required
from pgadmin.utils.driver import get_driver

from config import PG_DEFAULT_DRIVER


class ExclusionConstraintModule(ConstraintTypeModule):
    """
    class ForeignKeyConstraintModule(CollectionNodeModule)

        A module class for Exclusion constraint node derived from ConstraintTypeModule.

    Methods:
    -------
    * __init__(*args, **kwargs)
      - Method is used to initialize the ForeignKeyConstraintModule and it's base module.

    * get_nodes(gid, sid, did)
      - Method is used to generate the browser collection node.

    * node_inode()
      - Method is overridden from its base class to make the node as leaf node.

    * script_load()
      - Load the module script for language, when any of the database node is
        initialized.
    """

    NODE_TYPE = 'exclusion_constraint'
    COLLECTION_LABEL = _("Exclusion Constraints")

    def __init__(self, *args, **kwargs):
        """
        Method is used to initialize the ForeignKeyConstraintModule and it's base module.

        Args:
          *args:
          **kwargs:

        Returns:

        """
        self.min_ver = None
        self.max_ver = None
        super(ExclusionConstraintModule, self).__init__(*args, **kwargs)

    def get_nodes(self, gid, sid, did, scid, tid):
        """
        Generate the collection node
        """
        pass

    @property
    def node_inode(self):
        """
        Override this property to make the node a leaf node.

        Returns: False as this is the leaf node
        """
        return False

    @property
    def script_load(self):
        """
        Load the module script for exclusion_constraint, when any of the table node is
        initialized.

        Returns: node type of the server module.
        """
        return database.DatabaseModule.NODE_TYPE


blueprint = ExclusionConstraintModule(__name__)


class ExclusionConstraintView(PGChildNodeView):
    """
    class ExclusionConstraintView(PGChildNodeView)

        A view class for Exclusion constraint node derived from PGChildNodeView. This class is
        responsible for all the stuff related to view like creating, updating Exclusion constraint
        node, showing properties, showing sql in sql pane.

    Methods:
    -------
    * __init__(**kwargs)
      - Method is used to initialize the ForeignKeyConstraintView and it's base view.

    * module_js()
      - This property defines (if javascript) exists for this node.
        Override this property for your own logic

    * check_precondition()
      - This function will behave as a decorator which will checks
        database connection before running view, it will also attaches
        manager,conn & template_path properties to self

    * end_transaction()
      - To end any existing database transaction.

    * list()
      - This function returns Exclusion constraint nodes within that
        collection as http response.

    * get_list()
      - This function is used to list all the language nodes within that collection
        and return list of Exclusion constraint nodes.

    * nodes()
      - This function returns child node within that collection.
        Here return all Exclusion constraint node as http response.

    * get_nodes()
      - returns all Exclusion constraint nodes' list.

    * properties()
      - This function will show the properties of the selected Exclusion.

    * update()
      - This function will update the data for the selected Exclusion.

    * msql()
      - This function is used to return modified SQL for the selected Exclusion.

    * get_sql()
      - This function will generate sql from model data.

    * sql():
      - This function will generate sql to show it in sql pane for the selected Exclusion.

    * get_access_methods():
      - Returns access methods for exclusion constraint.

    * get_oper_class():
      - Returns operator classes for selected access method.

    * get_operator():
      - Returns operators for selected column.

    """

    node_type = 'exclusion_constraint'

    parent_ids = [
        {'type': 'int', 'id': 'gid'},
        {'type': 'int', 'id': 'sid'},
        {'type': 'int', 'id': 'did'},
        {'type': 'int', 'id': 'scid'},
        {'type': 'int', 'id': 'tid'}
    ]
    ids = [{'type': 'int', 'id': 'exid'}
           ]

    operations = dict({
        'obj': [
            {'get': 'properties', 'delete': 'delete', 'put': 'update'},
            {'get': 'list', 'post': 'create'}
        ],
        'delete': [{'delete': 'delete'}],
        'children': [{'get': 'children'}],
        'nodes': [{'get': 'node'}, {'get': 'nodes'}],
        'sql': [{'get': 'sql'}],
        'msql': [{'get': 'msql'}, {'get': 'msql'}],
        'stats': [{'get': 'statistics'}],
        'module.js': [{}, {}, {'get': 'module_js'}]
    })

    def module_js(self):
        """
        This property defines (if javascript) exists for this node.
        Override this property for your own logic.
        """
        return make_response(
            render_template(
                "exclusion_constraint/js/exclusion_constraint.js",
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
                kwargs['sid']
            )
            self.conn = self.manager.connection(did=kwargs['did'])

            # If DB not connected then return error to browser
            if not self.conn.connected():
                return precondition_required(
                    _(
                        "Connection to the server has been lost!"
                    )
                )

            ver = self.manager.version

            if ver >= 90200:
                self.template_path = 'exclusion_constraint/sql/9.2_plus'
            elif ver >= 90100:
                self.template_path = 'exclusion_constraint/sql/9.1_plus'

            # We need parent's name eg table name and schema name
            SQL = render_template("/".join([self.template_path,
                                            'get_parent.sql']),
                                  tid=kwargs['tid'])
            status, rset = self.conn.execute_2darray(SQL)
            if not status:
                return internal_server_error(errormsg=rset)

            for row in rset['rows']:
                self.schema = row['schema']
                self.table = row['table']
            return f(*args, **kwargs)

        return wrap

    def end_transaction(self):
        SQL = render_template(
            "/".join([self.template_path, 'end.sql']))
        # End transaction if any.
        self.conn.execute_scalar(SQL)

    @check_precondition
    def properties(self, gid, sid, did, scid, tid, exid=None):
        """
        This function is used to list all the Exclusion constraint
        nodes within that collection.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        try:
            sql = render_template("/".join([self.template_path, 'properties.sql']),
                                  tid=tid, cid=exid)

            status, res = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=res)

            result = res['rows'][0]

            sql = render_template(
                "/".join([self.template_path, 'get_constraint_cols.sql']),
                cid=exid,
                colcnt=result['indnatts'])
            status, res = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=res)

            columns = []
            for row in res['rows']:
                if row['options'] & 1:
                    order = False
                    nulls_order = True if (row['options'] & 2) else False
                else:
                    order = True
                    nulls_order = True if (row['options'] & 2) else False

                columns.append({"column": row['coldef'].strip('"'),
                                "oper_class": row['opcname'],
                                "order": order,
                                "nulls_order": nulls_order,
                                "operator": row['oprname'],
                                "col_type": row['datatype']
                                })

            result['columns'] = columns

            return ajax_response(
                response=result,
                status=200
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def list(self, gid, sid, did, scid, tid, exid=None):
        """
        This function returns all exclusion constraints
        nodes within that collection as a http response.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        try:
            res = self.get_node_list(gid, sid, did, scid, tid, exid)
            return ajax_response(
                response=res,
                status=200
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def get_node_list(self, gid, sid, did, scid, tid, exid=None):
        """
        This function returns all exclusion constraints
        nodes within that collection as a list.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        SQL = render_template("/".join([self.template_path,
                                        'properties.sql']),
                              tid=tid)
        status, res = self.conn.execute_dict(SQL)

        return res['rows']

    @check_precondition
    def nodes(self, gid, sid, did, scid, tid, exid=None):
        """
        This function returns all Exclusion constraint nodes as a
        http response.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        try:
            res = self.get_nodes(gid, sid, did, scid, tid, exid)
            return make_json_response(
                data=res,
                status=200
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def get_nodes(self, gid, sid, did, scid, tid, exid=None):
        """
        This function returns all Exclusion constraint nodes as a list.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        res = []
        SQL = render_template("/".join([self.template_path,
                                        'nodes.sql']),
                              tid=tid)
        status, rset = self.conn.execute_2darray(SQL)

        for row in rset['rows']:
            res.append(
                self.blueprint.generate_browser_node(
                    row['oid'],
                    tid,
                    row['name'],
                    icon="icon-exclusion_constraint"
                ))
        return res

    @check_precondition
    def create(self, gid, sid, did, scid, tid, exid=None):
        """
        This function will create a Exclusion constraint.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        required_args = ['columns']

        data = request.form if request.form else json.loads(request.data.decode())

        for k, v in data.items():
            try:
                data[k] = json.loads(v)
            except (ValueError, TypeError):
                data[k] = v

        for arg in required_args:
            if arg not in data:
                return make_json_response(
                    status=400,
                    success=0,
                    errormsg=_(
                        "Couldn't find required parameter (%s)." % str(arg)
                    )
                )
            elif isinstance(data[arg], list) and len(data[arg]) < 1:
                return make_json_response(
                    status=400,
                    success=0,
                    errormsg=_(
                        "Couldn't find required parameter (%s)." % str(arg)
                    )
                )

        data['schema'] = self.schema
        data['table'] = self.table
        try:
            if 'name' not in data or data['name'] == "":
                SQL = render_template(
                    "/".join([self.template_path, 'begin.sql']))
                # Start transaction.
                status, res = self.conn.execute_scalar(SQL)
                if not status:
                    self.end_transaction()
                    return internal_server_error(errormsg=res)

            # The below SQL will execute CREATE DDL only
            SQL = render_template(
                "/".join([self.template_path, 'create.sql']),
                data=data, conn=self.conn
            )
            status, res = self.conn.execute_scalar(SQL)
            if not status:
                self.end_transaction()
                return internal_server_error(errormsg=res)

            if 'name' not in data or data['name'] == "":
                sql = render_template(
                    "/".join([self.template_path,
                              'get_oid_with_transaction.sql']),
                    tid=tid)

                status, res = self.conn.execute_dict(sql)
                if not status:
                    self.end_transaction()
                    return internal_server_error(errormsg=res)

                self.end_transaction()

                data['name'] = res['rows'][0]['name']

            else:
                sql = render_template("/".join([self.template_path, 'get_oid.sql']), name=data['name'])
                status, res = self.conn.execute_dict(sql)
                if not status:
                    self.end_transaction()
                    return internal_server_error(errormsg=res)

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    res['rows'][0]['oid'],
                    tid,
                    data['name'],
                    icon="icon-exclusion_constraint"
                )
            )

        except Exception as e:
            self.end_transaction()

            return make_json_response(
                status=400,
                success=0,
                errormsg=e
            )

    @check_precondition
    def update(self, gid, sid, did, scid, tid, exid=None):
        """
        This function will update the data for the selected
        Exclusion constraint.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        data = request.form if request.form else json.loads(request.data.decode())

        try:
            data['schema'] = self.schema
            data['table'] = self.table
            sql = self.get_sql(data, tid, exid)
            sql = sql.strip('\n').strip(' ')
            if sql != "":
                status, res = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                sql = render_template("/".join([self.template_path, 'get_oid.sql']), name=data['name'])
                status, res = self.conn.execute_dict(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                return make_json_response(
                    success=1,
                    info="Exclusion constraint updated",
                    data={
                        'id': res['rows'][0]['oid'],
                        'tid': tid,
                        'scid': scid,
                        'sid': sid,
                        'gid': gid,
                        'did': did,
                    }
                )
            else:
                return make_json_response(
                    success=1,
                    info="Nothing to update",
                    data={
                        'id': exid,
                        'tid': tid,
                        'scid': scid,
                        'sid': sid,
                        'gid': gid,
                        'did': did
                    }
                )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def delete(self, gid, sid, did, scid, tid, exid=None):
        """
        This function will delete an existing Exclusion.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        # Below code will decide if it's simple drop or drop with cascade call
        if self.cmd == 'delete':
            # This is a cascade operation
            cascade = True
        else:
            cascade = False
        try:
            sql = render_template("/".join([self.template_path, 'get_name.sql']),
                                  cid=exid)
            status, res = self.conn.execute_dict(sql)
            if not status:
                return internal_server_error(errormsg=res)

            data = res['rows'][0]
            data['schema'] = self.schema
            data['table'] = self.table

            sql = render_template("/".join([self.template_path, 'delete.sql']),
                                  data=data,
                                  cascade=cascade)
            status, res = self.conn.execute_scalar(sql)
            if not status:
                return internal_server_error(errormsg=res)

            return make_json_response(
                success=1,
                info=_("Exclusion constraint dropped."),
                data={
                    'id': exid,
                    'sid': sid,
                    'gid': gid,
                    'did': did
                }
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def msql(self, gid, sid, did, scid, tid, exid=None):
        """
        This function returns modified SQL for the selected
        Exclusion constraint.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        data = {}
        for k, v in request.args.items():
            try:
                data[k] = json.loads(v)
            except ValueError:
                data[k] = v

        data['schema'] = self.schema
        data['table'] = self.table
        try:
            sql = self.get_sql(data, tid, exid)
            sql = sql.strip('\n').strip(' ')

            return make_json_response(
                data=sql,
                status=200
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    def get_sql(self, data, tid, exid=None):
        """
        This function will generate sql from model data.

        Args:
          data: Contains the data of the selected Exclusion constraint.
          tid: Table ID.
          exid: Exclusion constraint ID

        Returns:

        """
        if exid is not None:
            sql = render_template("/".join([self.template_path, 'properties.sql']),
                                  tid=tid,
                                  cid=exid)
            status, res = self.conn.execute_dict(sql)
            if not status:
                return internal_server_error(errormsg=res)

            old_data = res['rows'][0]
            required_args = ['name']
            for arg in required_args:
                if arg not in data:
                    data[arg] = old_data[arg]

            sql = render_template("/".join([self.template_path, 'update.sql']),
                                  data=data, o_data=old_data)
        else:
            required_args = ['columns']

            for arg in required_args:
                if arg not in data:
                    return _('-- definition incomplete')
                elif isinstance(data[arg], list) and len(data[arg]) < 1:
                    return _('-- definition incomplete')

            sql = render_template("/".join([self.template_path, 'create.sql']),
                                  data=data, conn=self.conn)

        return sql

    @check_precondition
    def sql(self, gid, sid, did, scid, tid, exid=None):
        """
        This function generates sql to show in the sql pane for the selected
        Exclusion constraint.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          exid: Exclusion constraint ID

        Returns:

        """
        try:
            SQL = render_template(
                "/".join([self.template_path, 'properties.sql']),
                tid=tid, conn=self.conn, cid=exid)
            status, result = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=result)

            data = result['rows'][0]
            data['schema'] = self.schema
            data['table'] = self.table

            sql = render_template(
                "/".join([self.template_path, 'get_constraint_cols.sql']),
                cid=exid,
                colcnt=data['indnatts'])
            status, res = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=res)

            columns = []
            for row in res['rows']:
                if row['options'] & 1:
                    order = False
                    nulls_order = True if (row['options'] & 2) else False
                else:
                    order = True
                    nulls_order = True if (row['options'] & 2) else False

                columns.append({"column": row['coldef'].strip('"'),
                                "oper_class": row['opcname'],
                                "order": order,
                                "nulls_order": nulls_order,
                                "operator": row['oprname']
                                })

            data['columns'] = columns

            if not data['amname'] or data['amname'] == '':
                data['amname'] = 'btree'

            SQL = render_template(
                "/".join([self.template_path, 'create.sql']), data=data)

            sql_header = "-- Constraint: {0}\n\n-- ".format(data['name'])

            sql_header += render_template(
                "/".join([self.template_path, 'delete.sql']),
                data=data)
            sql_header += "\n"

            SQL = sql_header + SQL

            return ajax_response(response=SQL)

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def statistics(self, gid, sid, did, scid, tid, exid):
        """
        Statistics

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Exclusion constraint ID

        Returns the statistics for a particular object if cid is specified
        """

        # Check if pgstattuple extension is already created?
        # if created then only add extended stats
        status, is_pgstattuple = self.conn.execute_scalar("""
        SELECT (count(extname) > 0) AS is_pgstattuple
        FROM pg_extension
        WHERE extname='pgstattuple'
        """)
        if not status:
            return internal_server_error(errormsg=is_pgstattuple)

        if is_pgstattuple:
            # Fetch index details only if extended stats available
            SQL = render_template(
                "/".join([self.template_path, 'properties.sql']),
                tid=tid, conn=self.conn, cid=exid)
            status, result = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=result)

            data = result['rows'][0]
            name = data['name']
        else:
            name = None

        status, res = self.conn.execute_dict(
            render_template(
                "/".join([self.template_path, 'stats.sql']),
                conn=self.conn, schema=self.schema,
                name=name, exid=exid, is_pgstattuple=is_pgstattuple
            )
        )
        if not status:
            return internal_server_error(errormsg=res)

        return make_json_response(
            data=res,
            status=200
        )


constraint = ConstraintRegistry(
    'exclusion_constraint', ExclusionConstraintModule, ExclusionConstraintView
)
ExclusionConstraintView.register_node_view(blueprint)
