##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""A blueprint module implementing the datagrid frame."""
MODULE_NAME = 'datagrid'

import json
import pickle
import random

from flask import Response, url_for, session, request, make_response
from flask import current_app as app
from flask.ext.babel import gettext
from flask.ext.security import login_required
from pgadmin.tools.sqleditor.command import *
from pgadmin.utils import PgAdminModule
from pgadmin.utils.ajax import make_json_response, bad_request, \
    internal_server_error

from config import PG_DEFAULT_DRIVER


class DataGridModule(PgAdminModule):
    """
    class DataGridModule(PgAdminModule)

        A module class for Edit Grid derived from PgAdminModule.
    """

    LABEL = "Data Grid"

    def get_own_menuitems(self):
        return {}

    def get_own_javascripts(self):
        return [{
            'name': 'pgadmin.datagrid',
            'path': url_for('datagrid.index') + "datagrid",
            'when': None
        }]

    def get_panels(self):
        return []


blueprint = DataGridModule(MODULE_NAME, __name__, static_url_path='/static')


@blueprint.route("/")
@login_required
def index():
    return bad_request(errormsg=gettext('This URL cannot be requested directly.'))


@blueprint.route("/css/datagrid.css")
def datagrid_css():
    return make_response(
        render_template('datagrid/css/datagrid.css'),
        200, {'Content-Type': 'text/css'}
    )


@blueprint.route("/filter")
@login_required
def show_filter():
    return render_template(MODULE_NAME + '/filter.html')


@blueprint.route(
    '/initialize/datagrid/<int:cmd_type>/<obj_type>/<int:sid>/<int:did>/<int:obj_id>',
    methods=["PUT", "POST"]
)
@login_required
def initialize_datagrid(cmd_type, obj_type, sid, did, obj_id):
    """
    This method is responsible for creating an asynchronous connection.
    After creating the connection it will instantiate and initialize
    the object as per the object type. It will also create a unique
    transaction id and store the information into session variable.

    Args:
        cmd_type: Contains value for which menu item is clicked.
        obj_type: Contains type of selected object for which data grid to be render
        sid: Server Id
        did: Database Id
        obj_id: Id of currently selected object
    """

    if request.data:
        filter_sql = json.loads(request.data.decode())
    else:
        filter_sql = request.args or request.form

    # Create asynchronous connection using random connection id.
    conn_id = str(random.randint(1, 9999999))
    try:
        manager = get_driver(PG_DEFAULT_DRIVER).connection_manager(sid)
        conn = manager.connection(did=did, conn_id=conn_id)
    except Exception as e:
        return internal_server_error(errormsg=str(e))

    # Connect the Server
    status, msg = conn.connect()
    if not status:
        return internal_server_error(errormsg=str(msg))

    try:
        # Get the object as per the object type
        command_obj = ObjectRegistry.get_object(obj_type, conn_id=conn_id, sid=sid,
                                                did=did, obj_id=obj_id, cmd_type=cmd_type,
                                                sql_filter=filter_sql)
    except Exception as e:
        return internal_server_error(errormsg=str(e))

    # Create a unique id for the transaction
    trans_id = str(random.randint(1, 9999999))

    if 'gridData' not in session:
        sql_grid_data = dict()
    else:
        sql_grid_data = session['gridData']

    # Use pickle to store the command object which will be used
    # later by the sql grid module.
    sql_grid_data[trans_id] = {
        'command_obj': pickle.dumps(command_obj, -1)  # -1 specify the highest protocol version available
    }

    # Store the grid dictionary into the session variable
    session['gridData'] = sql_grid_data

    return make_json_response(data={'gridTransId': trans_id})


@blueprint.route('/panel/<int:trans_id>/<is_query_tool>/<path:editor_title>', methods=["GET"])
def panel(trans_id, is_query_tool, editor_title):
    """
    This method calls index.html to render the data grid.

    Args:
        trans_id: unique transaction id
        is_query_tool: True if panel calls when query tool menu is clicked.
        editor_title: Title of the editor
    """
    # Let's fetch Script type URL from request
    if request.args and request.args['query_url'] != '':
        sURL = request.args['query_url']
    else:
        sURL = None

    """
    Animations and transitions are not automatically GPU accelerated and by default use browser's slow rendering engine.
    We need to set 'translate3d' value of '-webkit-transform' property in order to use GPU.
    After applying this property under linux, Webkit calculates wrong position of the elements so panel contents are not visible.
    To make it work, we need to explicitly set '-webkit-transform' property to 'none' for .ajs-notifier, .ajs-message, .ajs-modal classes.

    This issue is only with linux runtime application and observed in Query tool and debugger.
    When we open 'Open File' dialog then whole Query-tool panel content is not visible though it contains HTML element in back end.

    The port number should have already been set by the runtime if we're running in desktop mode.
    """
    is_linux_platform = False

    from sys import platform as _platform
    if "linux" in _platform:
        is_linux_platform = True

    return render_template("datagrid/index.html", _=gettext, uniqueId=trans_id,
                           is_query_tool=is_query_tool, editor_title=editor_title,
                           script_type_url=sURL, is_desktop_mode=app.PGADMIN_RUNTIME,
                           is_linux=is_linux_platform)


@blueprint.route(
    '/initialize/query_tool/<int:sid>/<int:did>',
    methods=["POST"]
)
@blueprint.route(
    '/initialize/query_tool/<int:sid>',
    methods=["POST"]
)
@login_required
def initialize_query_tool(sid, did=None):
    """
    This method is responsible for instantiating and initializing
    the query tool object. It will also create a unique
    transaction id and store the information into session variable.

    Args:
        sid: Server Id
        did: Database Id
    """

    if did is None:
        # Use Maintenance database OID
        from pgadmin.utils.driver import get_driver
        driver = get_driver(PG_DEFAULT_DRIVER)
        manager = driver.connection_manager(sid)
        conn = manager.connection()
        if conn.connected():
            did = manager.did
        else:
            internal_server_error(
                errormsg=gettext(
                    'Server disconnected, Please connect and try again'
                )
            )

    try:
        command_obj = ObjectRegistry.get_object('query_tool', sid=sid, did=did)
    except Exception as e:
        return internal_server_error(errormsg=str(e))

    # Create a unique id for the transaction
    trans_id = str(random.randint(1, 9999999))

    if 'gridData' not in session:
        sql_grid_data = dict()
    else:
        sql_grid_data = session['gridData']

    # Use pickle to store the command object which will be used
    # later by the sql grid module.
    sql_grid_data[trans_id] = {
        'command_obj': pickle.dumps(command_obj, -1)  # -1 specify the highest protocol version available
    }

    # Store the grid dictionary into the session variable
    session['gridData'] = sql_grid_data

    return make_json_response(data={'gridTransId': trans_id})


@blueprint.route('/close/<int:trans_id>', methods=["GET"])
def close(trans_id):
    """
    This method is used to close the asynchronous connection
    and remove the information of unique transaction id from
    the session variable.

    Args:
        trans_id: unique transaction id
    """

    grid_data = session['gridData']
    # Return from the function if transaction id not found
    if str(trans_id) not in grid_data:
        return make_json_response(data={'status': True})

    cmd_obj_str = grid_data[str(trans_id)]['command_obj']
    # Use pickle.loads function to get the command object
    cmd_obj = pickle.loads(cmd_obj_str)

    # if connection id is None then no need to release the connection
    if cmd_obj.conn_id is not None:
        try:
            manager = get_driver(PG_DEFAULT_DRIVER).connection_manager(cmd_obj.sid)
            conn = manager.connection(did=cmd_obj.did, conn_id=cmd_obj.conn_id)
        except Exception as e:
            return internal_server_error(errormsg=str(e))

        # Release the connection
        if conn.connected():
            manager.release(did=cmd_obj.did, conn_id=cmd_obj.conn_id)

        # Remove the information of unique transaction id from the session variable.
        grid_data.pop(str(trans_id), None)
        session['gridData'] = grid_data

    return make_json_response(data={'status': True})


@blueprint.route('/filter/validate/<int:sid>/<int:did>/<int:obj_id>',
                 methods=["PUT", "POST"])
@login_required
def validate_filter(sid, did, obj_id):
    """
    This method is used to validate the sql filter.

    Args:
        sid: Server Id
        did: Database Id
        obj_id: Id of currently selected object
    """
    if request.data:
        filter_sql = json.loads(request.data.decode())
    else:
        filter_sql = request.args or request.form

    try:
        # Create object of SQLFilter class
        sql_filter_obj = SQLFilter(sid=sid, did=did, obj_id=obj_id)

        # Call validate_filter method to validate the SQL.
        status, res = sql_filter_obj.validate_filter(filter_sql)
    except Exception as e:
        return internal_server_error(errormsg=str(e))

    return make_json_response(data={'status': status, 'result': res})


@blueprint.route("/datagrid.js")
@login_required
def script():
    """render the required javascript"""
    return Response(response=render_template("datagrid/js/datagrid.js", _=gettext),
                    status=200,
                    mimetype="application/javascript")
