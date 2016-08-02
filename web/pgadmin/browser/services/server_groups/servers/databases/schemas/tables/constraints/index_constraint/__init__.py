##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Implements Primary key constraint Node"""

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


class IndexConstraintModule(ConstraintTypeModule):
    """
    class IndexConstraintModule(CollectionNodeModule)

        A module class for Primary key constraint node derived from ConstraintTypeModule.

    Methods:
    -------
    * __init__(*args, **kwargs)
      - Method is used to initialize the PrimaryKeyConstraintModule and it's base module.

    * get_nodes(gid, sid, did)
      - Method is used to generate the browser collection node.

    * node_inode()
      - Method is overridden from its base class to make the node as leaf node.

    * script_load()
      - Load the module script for language, when any of the database node is
        initialized.
    """

    NODE_TYPE = 'Index constraint'
    COLLECTION_LABEL = _('index_constraint')

    def __init__(self, *args, **kwargs):
        """
        Method is used to initialize the PrimaryKeyConstraintModule and it's base module.

        Args:
          *args:
          **kwargs:

        Returns:

        """
        self.min_ver = None
        self.max_ver = None
        super(IndexConstraintModule, self).__init__(*args, **kwargs)

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
        Load the module script for primary_key, when any of the table node is
        initialized.

        Returns: node type of the server module.
        """
        return database.DatabaseModule.NODE_TYPE


class PrimaryKeyConstraintModule(IndexConstraintModule):
    """
     class PrimaryKeyConstraintModule(IndexConstraintModule)

        A module class for the catalog schema node derived from IndexConstraintModule.
    """

    NODE_TYPE = 'primary_key'
    COLLECTION_LABEL = _("Primary Key")


primary_key_blueprint = PrimaryKeyConstraintModule(__name__)


class UniqueConstraintModule(IndexConstraintModule):
    """
     class UniqueConstraintModule(IndexConstraintModule)

        A module class for the catalog schema node derived from IndexConstraintModule.
    """

    NODE_TYPE = 'unique_constraint'
    COLLECTION_LABEL = _("Unique Constraint")


unique_constraint_blueprint = UniqueConstraintModule(__name__)


class IndexConstraintView(PGChildNodeView):
    """
    class PrimaryKeyConstraintView(PGChildNodeView)

        A view class for Primary key constraint node derived from PGChildNodeView. This class is
        responsible for all the stuff related to view like creating, updating Primary key constraint
        node, showing properties, showing sql in sql pane.

    Methods:
    -------
    * __init__(**kwargs)
      - Method is used to initialize the PrimaryKeyConstraintView and it's base view.

    * module_js()
      - This property defines (if javascript) exists for this node.
        Override this property for your own logic

    * check_precondition()
      - This function will behave as a decorator which will checks
        database connection before running view, it will also attaches
        manager,conn & template_path properties to self

    * list()
      - This function returns primary key constraint nodes within that
        collection as http response.

    * get_list()
      - This function is used to list all the language nodes within that collection
        and return list of primary key constraint nodes.

    * nodes()
      - This function returns child node within that collection.
        Here return all primary key constraint node as http response.

    * get_nodes()
      - returns all primary key constraint nodes' list.

    * properties()
      - This function will show the properties of the selected primary key.

    * update()
      - This function will update the data for the selected primary key.

    * msql()
      - This function is used to return modified SQL for the selected primary key.

    * get_sql()
      - This function will generate sql from model data.

    * sql():
      - This function will generate sql to show it in sql pane for the selected primary key.

    * get_indices():
        - This function returns indices for current table.

    """

    node_type = 'index_constraint'

    node_label = _('Index constraint')

    parent_ids = [
        {'type': 'int', 'id': 'gid'},
        {'type': 'int', 'id': 'sid'},
        {'type': 'int', 'id': 'did'},
        {'type': 'int', 'id': 'scid'},
        {'type': 'int', 'id': 'tid'}
    ]
    ids = [{'type': 'int', 'id': 'cid'}
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
        'dependency': [{'get': 'dependencies'}],
        'dependent': [{'get': 'dependents'}],
        'module.js': [{}, {}, {'get': 'module_js'}]
    })

    def module_js(self):
        """
        This property defines (if javascript) exists for this node.
        Override this property for your own logic.
        """
        return make_response(
            render_template(
                "index_constraint/js/index_constraint.js",
                _=_,
                node_type=self.node_type,
                node_label=self.node_label
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

            self.template_path = 'index_constraint/sql'
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
    def properties(self, gid, sid, did, scid, tid, cid=None):
        """
        This function is used to list all the primary key
        nodes within that collection.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        sql = render_template("/".join([self.template_path, 'properties.sql']),
                              tid=tid,
                              cid=cid,
                              constraint_type=self.constraint_type)
        status, res = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=res)

        result = res['rows'][0]

        sql = render_template(
            "/".join([self.template_path, 'get_constraint_cols.sql']),
            cid=cid,
            colcnt=result['indnatts'])
        status, res = self.conn.execute_dict(sql)

        if not status:
            return internal_server_error(errormsg=res)

        columns = []
        for row in res['rows']:
            columns.append({"column": row['column'].strip('"')})

        result['columns'] = columns

        return ajax_response(
            response=result,
            status=200
        )

    @check_precondition
    def list(self, gid, sid, did, scid, tid, cid=None):
        """
        This function returns all primary keys
        nodes within that collection as a http response.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        try:
            res = self.get_node_list(gid, sid, did, scid, tid, cid)
            return ajax_response(
                response=res,
                status=200
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def get_node_list(self, gid, sid, did, scid, tid, cid=None):
        """
        This function returns all primary keys
        nodes within that collection as a list.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        SQL = render_template("/".join([self.template_path, 'properties.sql']),
                              tid=tid,
                              constraint_type=self.constraint_type)
        status, res = self.conn.execute_dict(SQL)

        return res['rows']

    @check_precondition
    def nodes(self, gid, sid, did, scid, tid, cid=None):
        """
        This function returns all event trigger nodes as a
        http response.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        try:
            res = self.get_nodes(gid, sid, did, scid, tid, cid)
            return make_json_response(
                data=res,
                status=200
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def get_nodes(self, gid, sid, did, scid, tid, cid=None):
        """
        This function returns all event trigger nodes as a list.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        res = []
        SQL = render_template("/".join([self.template_path, 'nodes.sql']),
                              tid=tid,
                              constraint_type=self.constraint_type)
        status, rset = self.conn.execute_2darray(SQL)

        for row in rset['rows']:
            res.append(
                self.blueprint.generate_browser_node(
                    row['oid'],
                    tid,
                    row['name'],
                    icon="icon-%s" % self.node_type
                ))
        return res

    @check_precondition
    def create(self, gid, sid, did, scid, tid, cid=None):
        """
        This function will create a primary key.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        required_args = [
            [u'columns', u'index']  # Either of one should be there.
        ]

        data = request.form if request.form else json.loads(request.data.decode())

        for k, v in data.items():
            try:
                data[k] = json.loads(v)
            except (ValueError, TypeError):
                data[k] = v

        for arg in required_args:
            if isinstance(arg, list):
                for param in arg:
                    if (param in data and
                            (not isinstance(data[param], list) or
                                 (isinstance(data[param], list) and
                                          len(data[param]) > 0))):
                        break
                else:
                    return make_json_response(
                        status=400,
                        success=0,
                        errormsg=_(
                            "Couldn't find at least one required parameter (%s)." % str(param)
                        )
                    )

            elif arg not in data:
                return make_json_response(
                    status=400,
                    success=0,
                    errormsg=_(
                        "Couldn't find the required parameter (%s)." % arg
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
                data=data, conn=self.conn,
                constraint_name=self.constraint_name
            )

            status, msg = self.conn.execute_scalar(SQL)
            if not status:
                self.end_transaction()
                return internal_server_error(errormsg=msg)

            if 'name' not in data or data['name'] == "":
                sql = render_template(
                    "/".join([self.template_path,
                              'get_oid_with_transaction.sql'],
                             ),
                    constraint_type=self.constraint_type,
                    tid=tid)

                status, res = self.conn.execute_dict(sql)
                if not status:
                    self.end_transaction()
                    return internal_server_error(errormsg=res)

                self.end_transaction()

                data['name'] = res['rows'][0]['name']

            else:
                sql = render_template("/".join([self.template_path, 'get_oid.sql']),
                                      tid=tid,
                                      constraint_type=self.constraint_type,
                                      name=data['name'])
                status, res = self.conn.execute_dict(sql)
                if not status:
                    self.end_transaction()
                    return internal_server_error(errormsg=res)

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    res['rows'][0]['oid'],
                    tid,
                    data['name'],
                    icon="icon-%s" % self.node_type
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
    def update(self, gid, sid, did, scid, tid, cid=None):
        """
        This function will update the data for the selected
        primary key.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        data = request.form if request.form else json.loads(request.data.decode())

        try:
            data['schema'] = self.schema
            data['table'] = self.table
            sql = self.get_sql(data, tid, cid)
            sql = sql.strip('\n').strip(' ')
            if sql != "":
                status, res = self.conn.execute_scalar(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                sql = render_template("/".join([self.template_path, 'get_oid.sql']),
                                      tid=tid,
                                      constraint_type=self.constraint_type,
                                      name=data['name'])
                status, res = self.conn.execute_dict(sql)
                if not status:
                    return internal_server_error(errormsg=res)

                return make_json_response(
                    success=1,
                    info="Constraint updated",
                    data={
                        'id': cid,
                        'tid': tid,
                        'scid': scid,
                        'sid': sid,
                        'gid': gid,
                        'did': did
                    }
                )
            else:
                return make_json_response(
                    success=1,
                    info="Nothing to update",
                    data={
                        'id': cid,
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
    def delete(self, gid, sid, did, scid, tid, cid=None):
        """
        This function will delete an existing primary key.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

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
                                  tid=tid,
                                  constraint_type=self.constraint_type,
                                  cid=cid)
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
                info=_("{0} dropped.".format(self.node_label)),
                data={
                    'id': cid,
                    'sid': sid,
                    'gid': gid,
                    'did': did
                }
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def msql(self, gid, sid, did, scid, tid, cid=None):
        """
        This function returns modified SQL for the selected
        primary key.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

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
            sql = self.get_sql(data, tid, cid)
            sql = sql.strip('\n').strip(' ')

            return make_json_response(
                data=sql,
                status=200
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    def get_sql(self, data, tid, cid=None):
        """
        This function will generate sql from model data.

        Args:
          data: Contains the data of the selected primary key constraint.
          tid: Table ID.
          cid: Primary key constraint ID

        Returns:

        """
        if cid is not None:
            sql = render_template("/".join([self.template_path, 'properties.sql']),
                                  tid=tid,
                                  cid=cid,
                                  constraint_type=self.constraint_type)
            status, res = self.conn.execute_dict(sql)
            if not status:
                return internal_server_error(errormsg=res)

            old_data = res['rows'][0]
            required_args = [u'name']
            for arg in required_args:
                if arg not in data:
                    data[arg] = old_data[arg]

            sql = render_template("/".join([self.template_path, 'update.sql']),
                                  data=data,
                                  o_data=old_data)
        else:
            required_args = [
                [u'columns', u'index']  # Either of one should be there.
            ]

            for arg in required_args:
                if isinstance(arg, list):
                    for param in arg:
                        if (param in data and
                                ((isinstance(data[param], str) and
                                          data[param] != "") or
                                     (isinstance(data[param], list) and
                                              len(data[param]) > 0))):
                            break
                    else:
                        return _('-- definition incomplete')

                elif arg not in data:
                    return _('-- definition incomplete')

            sql = render_template("/".join([self.template_path, 'create.sql']),
                                  data=data,
                                  conn=self.conn,
                                  constraint_name=self.constraint_name)

        return sql

    @check_precondition
    def sql(self, gid, sid, did, scid, tid, cid=None):
        """
        This function generates sql to show in the sql pane for the selected
        primary key.

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key constraint ID

        Returns:

        """
        try:
            SQL = render_template(
                "/".join([self.template_path, 'properties.sql']),
                tid=tid,
                conn=self.conn,
                cid=cid,
                constraint_type=self.constraint_type)
            status, res = self.conn.execute_dict(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            data = res['rows'][0]
            data['schema'] = self.schema
            data['table'] = self.table

            sql = render_template(
                "/".join([self.template_path, 'get_constraint_cols.sql']),
                cid=cid, colcnt=data['indnatts'])

            status, res = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=res)

            columns = []
            for row in res['rows']:
                columns.append({"column": row['column'].strip('"')})

            data['columns'] = columns

            SQL = render_template(
                "/".join([self.template_path, 'create.sql']),
                data=data,
                constraint_name=self.constraint_name)

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
    def statistics(self, gid, sid, did, scid, tid, cid):
        """
        Statistics

        Args:
          gid: Server Group ID
          sid: Server ID
          did: Database ID
          scid: Schema ID
          tid: Table ID
          cid: Primary key/Unique constraint ID

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
            sql = render_template("/".join([self.template_path, 'properties.sql']),
                                  tid=tid,
                                  cid=cid,
                                  constraint_type=self.constraint_type)
            status, res = self.conn.execute_dict(sql)

            if not status:
                return internal_server_error(errormsg=res)

            result = res['rows'][0]
            name = result['name']
        else:
            name = None

        status, res = self.conn.execute_dict(
            render_template(
                "/".join([self.template_path, 'stats.sql']),
                conn=self.conn, schema=self.schema,
                name=name, cid=cid, is_pgstattuple=is_pgstattuple
            )
        )
        if not status:
            return internal_server_error(errormsg=res)

        return make_json_response(
            data=res,
            status=200
        )


class PrimaryKeyConstraintView(IndexConstraintView):
    node_type = 'primary_key'

    node_label = _('Primary key')

    constraint_name = "PRIMARY KEY"

    constraint_type = "p"


class UniqueConstraintView(IndexConstraintView):
    node_type = 'unique_constraint'

    node_label = _('Unique constraint')

    constraint_name = "UNIQUE"

    constraint_type = "u"


primary_key_constraint = ConstraintRegistry(
    'primary_key', PrimaryKeyConstraintModule, PrimaryKeyConstraintView
)

unique_constraint = ConstraintRegistry(
    'unique_constraint', UniqueConstraintModule, UniqueConstraintView
)

PrimaryKeyConstraintView.register_node_view(primary_key_blueprint)
UniqueConstraintView.register_node_view(unique_constraint_blueprint)
