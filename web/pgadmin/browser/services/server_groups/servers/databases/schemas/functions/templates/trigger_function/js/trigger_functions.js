/* Create and Register Function Collection and Node. */
define(
        ['jquery', 'underscore', 'underscore.string',
         'pgadmin', 'pgadmin.browser', 'alertify',
          'pgadmin.browser.collection', 'pgadmin.browser.server.privilege'],
function($, _, S, pgAdmin, pgBrowser, alertify) {

  if (!pgBrowser.Nodes['coll-trigger_function']) {
    var trigger_functions = pgBrowser.Nodes['coll-trigger_function'] =
      pgBrowser.Collection.extend({
        node: 'trigger_function',
        label: '{{ _('Trigger functions') }}',
        type: 'coll-trigger_function',
        columns: ['name', 'funcowner', 'description'],
        hasStatistics: true
      });
  };

  if (!pgBrowser.Nodes['trigger_function']) {
    pgBrowser.Nodes['trigger_function'] = pgBrowser.Node.extend({
      type: 'trigger_function',
      sqlAlterHelp: 'plpgsql-trigger.html',
      sqlCreateHelp: 'plpgsql-trigger.html',
      dialogHelp: '{{ url_for('help.static', filename='trigger_function_dialog.html') }}',
      label: '{{ _('Trigger function') }}',
      collection_type: 'coll-trigger_function',
      hasSQL: true,
      hasDepends: true,
      hasStatistics: true,
      parent_type: ['schema', 'catalog'],
      Init: function(args) {
        /* Avoid mulitple registration of menus */
        if (this.initialized)
            return;

        this.initialized = true;

        pgBrowser.add_menus([{
          name: 'create_trigger_function_on_coll', node: 'coll-trigger_function', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Trigger function...') }}',
          icon: 'wcTabIcon icon-trigger_function', data: {action: 'create', check: true},
          enable: 'canCreate'
        },{
          name: 'create_trigger_function', node: 'trigger_function', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Trigger function...') }}',
          icon: 'wcTabIcon icon-trigger_function', data: {action: 'create', check: true},
          enable: 'canCreate'
        },{
          name: 'create_trigger_function', node: 'schema', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Trigger function...') }}',
          icon: 'wcTabIcon icon-trigger_function', data: {action: 'create', check: false},
          enable: 'canCreate'
        }
        ]);

      },
      canDrop: pgBrowser.Nodes['schema'].canChildDrop,
      canDropCascade: pgBrowser.Nodes['schema'].canChildDrop,
      model: pgBrowser.Node.Model.extend({
        initialize: function(attrs, args) {
          var isNew = (_.size(attrs) === 0);
          if (isNew) {
            // Set Selected Schema
            schema_id = args.node_info.schema._id
            this.set({'pronamespace': schema_id}, {silent: true});

            // Set Current User
            var userInfo = pgBrowser.serverInfo[args.node_info.server._id].user;
            this.set({'funcowner': userInfo.name}, {silent: true});
          }
          pgBrowser.Node.Model.prototype.initialize.apply(this, arguments);
        },
        defaults: {
          name: undefined,
          oid: undefined,
          xmin: undefined,
          funcowner: undefined,
          pronamespace: undefined,
          description: undefined,
          pronargs: undefined, /* Argument Count */
          proargs: undefined, /* Arguments */
          proargtypenames: undefined, /* Argument Signature */
          prorettypename: 'trigger', /* Return Type */
          lanname: 'plpgsql', /* Language Name in which function is being written */
          provolatile: undefined, /* Volatility */
          proretset: undefined, /* Return Set */
          proisstrict: undefined,
          prosecdef: undefined, /* Security of definer */
          proiswindow: undefined, /* Window Function ? */
          procost: undefined, /* Estimated execution Cost */
          prorows: undefined, /* Estimated number of rows */
          proleakproof: undefined,
          args: [],
          prosrc: undefined,
          prosrc_c: undefined,
          probin: '$libdir/',
          options: [],
          variables: [],
          proacl: undefined,
          seclabels: [],
          acl: [],
          sysfunc: undefined,
          sysproc: undefined
        },
        schema: [{
          id: 'name', label: '{{ _('Name') }}', cell: 'string',
          type: 'text', mode: ['properties', 'create', 'edit'],
          disabled: 'isDisabled'
        },{
          id: 'oid', label: '{{ _('OID') }}', cell: 'string',
          type: 'text' , mode: ['properties']
        },{
          id: 'funcowner', label: '{{ _('Owner') }}', cell: 'string',
          control: Backform.NodeListByNameControl, node: 'role',  type:
          'text', disabled: 'isDisabled'
        },{
          id: 'pronamespace', label: '{{ _('Schema') }}', cell: 'string',
          control: 'node-list-by-id', type: 'text', cache_level: 'database',
          node: 'schema', disabled: 'isDisabled', mode: ['create', 'edit']
        },{
          id: 'sysfunc', label: '{{ _('System function?') }}',
           cell:'boolean', type: 'switch',
           mode: ['properties'], visible: 'isVisible'
        },{
          id: 'sysproc', label: '{{ _('System procedure?') }}',
           cell:'boolean', type: 'switch',
           mode: ['properties'], visible: 'isVisible'
        },{
          id: 'description', label: '{{ _('Comment') }}', cell: 'string',
          type: 'multiline', disabled: 'isDisabled'
        },{
          id: 'pronargs', label: '{{ _('Argument count') }}', cell: 'string',
          type: 'text', group: '{{ _('Definition') }}', mode: ['properties']
        },{
          id: 'proargs', label: '{{ _('Arguments') }}', cell: 'string',
          type: 'text', group: '{{ _('Definition') }}', mode: ['properties', 'edit'],
          disabled: 'isDisabled'
        },{
          id: 'proargtypenames', label: '{{ _('Signature arguments') }}', cell:
          'string', type: 'text', group: '{{ _('Definition') }}', mode: ['properties'],
          disabled: 'isDisabled'
        },{
          id: 'prorettypename', label: '{{ _('Return type') }}', cell: 'string',
          control: 'select2', type: 'text', group: '{{ _('Definition') }}',
          disabled: 'isDisabled', first_empty: true,
          select2: { width: "100%", allowClear: false },
          mode: ['create'], visible: 'isVisible', options: [
            {label: 'trigger', value: 'trigger'},
            {label: 'event_trigger', value: 'event_trigger'}
          ]
        },{
          id: 'prorettypename', label: '{{ _('Return type') }}', cell: 'string',
          type: 'text', group: '{{ _('Definition') }}', disabled: true,
          mode: ['properties', 'edit'], disabled: 'isDisabled', visible: 'isVisible'
        },  {
          id: 'lanname', label: '{{ _('Language') }}', cell: 'string',
          control: 'node-ajax-options', type: 'text', group: '{{ _('Definition') }}',
          url: 'get_languages', disabled: 'isDisabled', transform: function(d, self) {
             return _.reject(d, function(o){ return o.label == 'sql' || o.label == 'edbspl'; });
          }, select2: { allowClear: false }
        },{
          id: 'prosrc', label: '{{ _('Code') }}', cell: 'string',
          type: 'text', mode: ['properties', 'create', 'edit'],
          group: '{{ _('Definition') }}', deps: ['lanname'],
          control: Backform.SqlFieldControl,
          extraClasses:['custom_height_css_class'],
          visible: function(m) {
            if (m.get('lanname') == 'c') {
              return false;
            }
            return true;
          }, disabled: 'isDisabled'
        },{
          id: 'probin', label: '{{ _('Object file') }}', cell: 'string',
          type: 'text', group: '{{ _('Definition') }}', deps: ['lanname'], visible:
          function(m) {
            if (m.get('lanname') == 'c') { return true; }
            return false;
          }, disabled: 'isDisabled'
        },{
          id: 'prosrc_c', label: '{{ _('Link symbol') }}', cell: 'string',
          type: 'text', group: '{{ _('Definition') }}',  deps: ['lanname'], visible:
          function(m) {
            if (m.get('lanname') == 'c') { return true; }
            return false;
          }, disabled: 'isDisabled'
        },{
          id: 'provolatile', label: '{{ _('Volatility') }}', cell: 'string',
          control: 'node-ajax-options', type: 'text', group: '{{ _('Options') }}',
          options:[
            {'label': 'VOLATILE', 'value': 'v'},
            {'label': 'STABLE', 'value': 's'},
            {'label': 'IMMUTABLE', 'value': 'i'},
          ], disabled: 'isDisabled', select2: { allowClear: false }
        },{
          id: 'proretset', label: '{{ _('Returns a set?') }}', type: 'switch',
          group: '{{ _('Options') }}', disabled: 'isDisabled',
          visible: 'isVisible'
        },{
          id: 'proisstrict', label: '{{ _('Strict?') }}', type: 'switch',
          disabled: 'isDisabled', group: '{{ _('Options') }}',
          options: {
            'onText': 'Yes', 'offText': 'No',
            'onColor': 'success', 'offColor': 'primary',
            'size': 'small'
           }
        },{
          id: 'prosecdef', label: '{{ _('Security of definer?') }}',
           group: '{{ _('Options') }}', cell:'boolean', type: 'switch',
           disabled: 'isDisabled'
        },{
          id: 'proiswindow', label: '{{ _('Window?') }}',
           group: '{{ _('Options') }}', cell:'boolean', type: 'switch',
            disabled: 'isDisabled', visible: 'isVisible'
        },{
          id: 'procost', label: '{{ _('Estimated cost') }}', type: 'text',
          group: '{{ _('Options') }}', disabled: 'isDisabled'
        },{
          id: 'prorows', label: '{{ _('Estimated rows') }}', type: 'text',
          group: '{{ _('Options') }}',
          disabled: 'isDisabled',
          deps: ['proretset'], visible: 'isVisible'
        },{
          id: 'proleakproof', label: '{{ _('Leak proof?') }}',
          group: '{{ _('Options') }}', cell:'boolean', type: 'switch', min_version: 90200,
          disabled: 'isDisabled'
        }, pgBrowser.SecurityGroupUnderSchema, {
          id: 'proacl', label: '{{ _('Privileges') }}', mode: ['properties'],
           group: '{{ _('Security') }}', type: 'text'
        },{
          id: 'variables', label: '{{ _('Parameters') }}', type: 'collection',
          group: '{{ _('Parameters') }}', control: 'variable-collection',
          model: pgBrowser.Node.VariableModel,
          mode: ['edit', 'create'], canAdd: 'canVarAdd', canEdit: false,
          canDelete: true, disabled: 'isDisabled'
         },{
          id: 'acl', label: '{{ _('Privileges') }}', editable: false,
          type: 'collection', group: 'security', mode: ['edit', 'create'],
          model: pgBrowser.Node.PrivilegeRoleModel.extend({
            privileges: ['X']
          }), uniqueCol : ['grantee', 'grantor'], disabled: 'isDisabled',
          canAdd: true, canDelete: true, control: 'unique-col-collection'
        },{
          id: 'seclabels', label: '{{ _('Security Labels') }}', canEdit: true,
          model: pgBrowser.SecLabelModel, type: 'collection',
          min_version: 90100, group: 'security', mode: ['edit', 'create'],
           canDelete: true, control: 'unique-col-collection', canAdd: true,
          uniqueCol : ['provider'], disabled: 'isDisabled'
        }],
        validate: function(keys)
        {
          var err = {},
              errmsg,
              seclabels = this.get('seclabels');

          // Nothing to validate
          if(keys && keys.length == 0) {
            this.errorModel.clear();
            return null;
          }

          if (_.isUndefined(this.get('name')) || String(this.get('name')).replace(/^\s+|\s+$/g, '') == '') {
            err['name'] = '{{ _('Name cannot be empty.') }}';
            errmsg = errmsg || err['name'];
          }

          if (_.isUndefined(this.get('funcowner')) || String(this.get('funcowner')).replace(/^\s+|\s+$/g, '') == '') {
            err['funcowner'] = '{{ _('Owner cannot be empty.') }}';
            errmsg = errmsg || err['funcowner'];
          }

          if (_.isUndefined(this.get('pronamespace')) || String(this.get('pronamespace')).replace(/^\s+|\s+$/g, '') == '') {
            err['pronamespace'] = '{{ _('Schema cannot be empty.') }}';
            errmsg = errmsg || err['pronamespace'];
          }

          if (_.isUndefined(this.get('prorettypename')) || String(this.get('prorettypename')).replace(/^\s+|\s+$/g, '') == '') {
            err['prorettypename'] = '{{ _('Return Type cannot be empty.') }}';
            errmsg = errmsg || err['prorettypename'];
          }

          if (_.isUndefined(this.get('lanname')) || String(this.get('lanname')).replace(/^\s+|\s+$/g, '') == '') {
            err['lanname'] = '{{ _('Language cannot be empty.') }}';
            errmsg = errmsg || err['lanname'];
          }

          if (String(this.get('lanname')) == 'c') {
            if (_.isUndefined(this.get('probin')) || String(this.get('probin'))
              .replace(/^\s+|\s+$/g, '') == '') {
              err['probin'] = '{{ _('Object File cannot be empty.') }}';
              errmsg = errmsg || err['probin'];
            }

            if (_.isUndefined(this.get('prosrc_c')) || String(this.get('prosrc_c')).replace(/^\s+|\s+$/g, '') == '') {
              err['prosrc_c'] = '{{ _('Link Symbol cannot be empty.') }}';
              errmsg = errmsg || err['prosrc_c'];
            }
          }
          else {
            if (_.isUndefined(this.get('prosrc')) || String(this.get('prosrc')).replace(/^\s+|\s+$/g, '') == '') {
              err['prosrc'] = '{{ _('Code cannot be empty.') }}';
              errmsg = errmsg || err['prosrc'];
            }
          }

          if (seclabels) {
            var secLabelsErr;
            for (var i = 0; i < seclabels.models.length && !secLabelsErr; i++) {
              secLabelsErr = (seclabels.models[i]).validate.apply(seclabels.models[i]);
              if (secLabelsErr) {
                err['seclabels'] = secLabelsErr;
                errmsg = errmsg || secLabelsErr;
              }
            }
          }

          this.errorModel.clear().set(err);

          if (_.size(err)) {
            this.trigger('on-status', {msg: errmsg});
            return errmsg;
          }

          return null;
        },
        isVisible: function(m){
          if (this.name == 'sysproc') { return false; }
          return true;
        },
        isDisabled: function(m){
          if(this.node_info &&  'catalog' in this.node_info) {
            return true;
          }
          name = this.name;
          switch(name){
            case 'proargs':
            case 'proargtypenames':
            case 'prorettypename':
            case 'proretset':
            case 'proiswindow':
              return !m.isNew();
              break;
            case 'prorows':
              if(m.get('proretset') == true) {
                return false;
              }
              else {
                return true;
              }
              break;
            default:
              return false;
              break;
          }
          return false;
        },
        canVarAdd: function(m) {
          if(this.node_info &&  'catalog' in this.node_info) {
            return false;
          }
         return true;
        }
      }),
      canCreate: function(itemData, item, data) {
        //If check is false then , we will allow create menu
        if (data && data.check == false)
          return true;

        var t = pgBrowser.tree, i = item, d = itemData;
        // To iterate over tree to check parent node
        while (i) {
          // If it is schema then allow user to create Function
          if (_.indexOf(['schema'], d._type) > -1)
            return true;

          if ('coll-trigger_function' == d._type) {
            //Check if we are not child of catalog
            prev_i = t.hasParent(i) ? t.parent(i) : null;
            prev_d = prev_i ? t.itemData(prev_i) : null;
            if( prev_d._type == 'catalog') {
              return false;
            } else {
              return true;
            }
          }
          i = t.hasParent(i) ? t.parent(i) : null;
          d = i ? t.itemData(i) : null;
        }
        // by default we do not want to allow create menu
        return true;
      }
  });

  }

  return pgBrowser.Nodes['trigger_function'];
});
