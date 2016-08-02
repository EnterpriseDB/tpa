define(
        ['jquery', 'underscore', 'underscore.string', 'pgadmin', 'pgadmin.browser', 'alertify', 'pgadmin.browser.collection', 'pgadmin.browser.node.ui', 'pgadmin.browser.server.privilege'],
function($, _, S, pgAdmin, pgBrowser, alertify) {

  if (!pgBrowser.Nodes['coll-tablespace']) {
    var databases = pgBrowser.Nodes['coll-tablespace'] =
      pgBrowser.Collection.extend({
        node: 'tablespace',
        label: '{{ _('Tablespaces') }}',
        type: 'coll-tablespace',
        columns: ['name', 'spcuser', 'description'],
        hasStatistics: true
      });
  };

  if (!pgBrowser.Nodes['tablespace']) {
    pgBrowser.Nodes['tablespace'] = pgBrowser.Node.extend({
      parent_type: 'server',
      type: 'tablespace',
      sqlAlterHelp: 'sql-altertablespace.html',
      sqlCreateHelp: 'sql-createtablespace.html',
      dialogHelp: '{{ url_for('help.static', filename='tablespace_dialog.html') }}',
      label: '{{ _('Tablespace') }}',
      hasSQL:  true,
      canDrop: true,
      hasDepends: true,
      hasStatistics: true,
      Init: function() {
        /* Avoid mulitple registration of menus */
        if (this.initialized)
            return;

        this.initialized = true;

        pgBrowser.add_menus([{
          name: 'create_tablespace_on_server', node: 'server', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Tablespace...') }}',
          icon: 'wcTabIcon icon-tablespace', data: {action: 'create'},
          enable: 'can_create_tablespace'
        },{
          name: 'create_tablespace_on_coll', node: 'coll-tablespace', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Tablespace...') }}',
          icon: 'wcTabIcon pg-icon-tablespace', data: {action: 'create'},
          enable: 'can_create_tablespace'
        },{
          name: 'create_tablespace', node: 'tablespace', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Tablespace...') }}',
          icon: 'wcTabIcon pg-icon-tablespace', data: {action: 'create'},
          enable: 'can_create_tablespace'
        },{
          name: 'move_tablespace', node: 'tablespace', module: this,
          applies: ['object', 'context'], callback: 'move_objects',
          category: 'move_tablespace', priority: 5,
          label: '{{ _('Move objects to...') }}',
          icon: 'fa fa-exchange', data: {action: 'create'},
          enable: 'can_move_objects'
        }
        ]);
      },
      can_create_tablespace: function(node, item) {
        var treeData = this.getTreeNodeHierarchy(item),
            server = treeData['server'];

        return server.connected && server.user.is_superuser;
      },
      can_move_objects: function(node, item) {
        var treeData = this.getTreeNodeHierarchy(item),
            server = treeData['server'];
        // Only supported PG9.4 and above version
        return server.connected &&
                server.user.is_superuser &&
                server.version >= 90400;
      },
      callbacks: {
        /* Move objects from one tablespace to another */
        move_objects: function(args){
          var input = args || {},
            obj = this,
            t = pgBrowser.tree,
            i = input.item || t.selected(),
            d = i && i.length == 1 ? t.itemData(i) : undefined,
            node = d && pgBrowser.Nodes[d._type],
            url = obj.generate_url(i, 'move_objects', d, true),
            msql_url = obj.generate_url(i, 'move_objects_sql', d, true);

          if (!d)
            return false;

          // Object model
          var objModel = Backbone.Model.extend({
              idAttribute: 'id',
              defaults: {
                new_tblspc: undefined,
                obj_type: 'all',
                user: undefined
              },
              schema: [{
                  id: 'tblspc', label: '{{ _('New tablespace') }}',
                  type: 'text', disabled: false, control: 'node-list-by-name',
                  node: 'tablespace', select2: {allowClear: false},
                  filter: function(o) {
                    return o && (o.label != d.label);
                  }
              },{
                  id: 'obj_type', label: '{{ _('Object type') }}',
                  type: 'text', disabled: false, control: 'select2',
                  select2: { allowClear: false, width: "100%" },
                  options: [
                    {label: "All", value: 'all'},
                    {label: "Tables", value: 'tables'},
                    {label: "Indexes", value: 'indexes'},
                    {label: "Materialized views", value: 'materialized_views'},
                  ]
              },{
                  id: 'user', label: '{{ _('Object owner') }}',
                  type: 'text', disabled: false, control: 'node-list-by-name',
                  node: 'role', select2: {allowClear: false}
              },{
                  id: 'sqltab', label: '{{ _('SQL') }}', group: '{{ _('SQL') }}',
                  type: 'text', disabled: false, control: Backform.SqlTabControl.extend({
                    initialize: function() {
                      // Initialize parent class
                      Backform.SqlTabControl.prototype.initialize.apply(this, arguments);
                    },
                    onTabChange: function(obj) {
                      // Fetch the information only if the SQL tab is visible at the moment.
                      if (this.dialog && obj.shown == this.tabIndex) {
                            var self = this,
                            args = self.model.toJSON();
                            // Add existing tablespace
                            args.old_tblspc = d.label;

                            // Fetches modified SQL
                            $.ajax({
                              url: msql_url,
                              type: 'GET',
                              cache: false,
                              data: args,
                              dataType: "json",
                              contentType: "application/json"
                            }).done(function(res) {
                              self.sqlCtrl.clearHistory();
                              self.sqlCtrl.setValue(res.data);
                              self.sqlCtrl.refresh();
                            }).fail(function() {
                              self.model.trigger('pgadmin-view:msql:error');
                            }).always(function() {
                              self.model.trigger('pgadmin-view:msql:fetched');
                            });
                      }
                    }
                  })
              }],
              validate: function() {
                  return null;
              }
          });

          if(!alertify.move_objects_dlg) {
            alertify.dialog('move_objects_dlg' ,function factory() {
              return {
                main: function() {
                 var title = '{{ _('Move objects to another tablespace') }} ';
                 this.set('title', title);
                },
                build: function() {
                  alertify.pgDialogBuild.apply(this);
                },
                setup:function() {
                  return {
                     buttons: [{
                       text: '', key: 27, className: 'btn btn-default pull-left fa fa-lg fa-question',
                       attrs:{name:'dialog_help', type:'button', label: '{{ _('Users') }}',
                       url: '{{ url_for('help.static', filename='move_objects.html') }}'}
                       },{
                       text: '{{ _('OK') }}', key: 27, className: 'btn btn-primary fa fa-lg fa-save pg-alertify-button'
                       },{
                       text: '{{ _('Cancel') }}', key: 27, className: 'btn btn-danger fa fa-lg fa-times pg-alertify-button'
                     }],
                     // Set options for dialog
                     options: {
                       //disable both padding and overflow control.
                       padding : !1,
                       overflow: !1,
                       modal: false,
                       resizable: true,
                       maximizable: true,
                       pinnable: false,
                       closableByDimmer: false
                     }
                   };
                },
                hooks: {
                  // Triggered when the dialog is closed
                  onclose: function() {
                    if (this.view) {
                      // clear our backform model/view
                      this.view.remove({data: true, internal: true, silent: true});
                    }
                  }
                },
                prepare: function() {
                  var self = this,
                    $container = $("<div class='move_objects'></div>");
                  //Disbale Okay button
                  this.__internal.buttons[1].element.disabled = true;
                  // Find current/selected node
                  var t = pgBrowser.tree,
                    i = t.selected(),
                    d = i && i.length == 1 ? t.itemData(i) : undefined,
                    node = d && pgBrowser.Nodes[d._type];

                  if (!d)
                    return;
                  // Create treeInfo
                  var treeInfo = node.getTreeNodeHierarchy.apply(node, [i]);
                  // Instance of backbone model
                  var newModel = new objModel({}, {node_info: treeInfo}),
                      fields = Backform.generateViewSchema(
                        treeInfo, newModel, 'create', node,
                        treeInfo.server, true
                      );

                  var view = this.view = new Backform.Dialog({
                    el: $container, model: newModel, schema: fields
                  });
                  // Add our class to alertify
                  $(this.elements.body.childNodes[0]).addClass(
                    'alertify_tools_dialog_properties obj_properties'
                  );
                  // Render dialog
                  view.render();

                  this.elements.content.appendChild($container.get(0));

                  // Listen to model & if filename is provided then enable Backup button
                  this.view.model.on('change', function() {
                    if (!_.isUndefined(this.get('tblspc')) && this.get('tblspc') !== '') {
                      this.errorModel.clear();
                      self.__internal.buttons[1].element.disabled = false;
                    } else {
                      self.__internal.buttons[1].element.disabled = true;
                      this.errorModel.set('tblspc', '{{ _('Please select tablespace') }}')
                    }
                  });
                },
                // Callback functions when click on the buttons of the Alertify dialogs
                callback: function(e) {
                  if (e.button.element.name == "dialog_help") {
                    e.cancel = true;
                    pgBrowser.showHelp(e.button.element.name, e.button.element.getAttribute('url'),
                      null, null, e.button.element.getAttribute('label'));
                    return;
                  }
                  if (e.button.text === '{{ _('OK') }}') {
                    var self = this,
                        args =  this.view.model.toJSON();
                        args.old_tblspc = d.label;
                    e.cancel = true;
                    alertify.confirm('{{ _('Move objects...') }}',
                      '{{ _('Are you sure you wish to move objects ') }}'
                      + '"' + args.old_tblspc + '"'
                      + '{{ _(' to ') }}'
                      + '"' + args.tblspc + '"?',
                      function() {
                        $.ajax({
                          url: url,
                          method:'PUT',
                          data:{'data': JSON.stringify(args) },
                          success: function(res) {
                            if (res.success) {
                              alertify.success(res.info);
                              self.close();
                            } else {
                              alertify.error(res.errormsg);
                            }
                          },
                          error: function(xhr, status, error) {
                            try {
                              var err = $.parseJSON(xhr.responseText);
                              if (err.success == 0) {
                                alertify.error(err.errormsg);
                              }
                            } catch (e) {}
                          }
                        });
                      },
                      function() {
                        // Do nothing as user cancel the operation
                      }
                    );
                  }
                }
              }
            });
          }
          alertify.move_objects_dlg(true).resizeTo('40%','50%');;
        }
      },
      model: pgBrowser.Node.Model.extend({
        defaults: {
          name: undefined,
          owner: undefined,
          comment: undefined,
          spclocation: undefined,
          spcoptions: [],
          spcacl: [],
          seclabels:[]
        },

        // Default values!
        initialize: function(attrs, args) {
          var isNew = (_.size(attrs) === 0);

          if (isNew) {
            var userInfo = pgBrowser.serverInfo[args.node_info.server._id].user;
            this.set({'spcuser': userInfo.name}, {silent: true});
          }
          pgBrowser.Node.Model.prototype.initialize.apply(this, arguments);
        },

        schema: [{
          id: 'name', label: '{{ _('Name') }}', cell: 'string',
          type: 'text'
        },{
          id: 'oid', label:'{{ _('OID') }}', cell: 'string',
          type: 'text', disabled: true, mode: ['properties']
        },{
          id: 'spclocation', label:'{{ _('Location') }}', cell: 'string',
          group: '{{ _('Definition') }}', type: 'text', mode: ['properties', 'edit','create'],
          disabled: function(m) {
            // To disabled it in edit mode,
            // We'll check if model is new if yes then disabled it
            return !m.isNew();
          }
        },{
          id: 'spcuser', label:'{{ _('Owner') }}', cell: 'string',
          type: 'text', control: 'node-list-by-name', node: 'role',
          select2: {allowClear: false}
        },{
          id: 'acl', label: '{{ _('Privileges') }}', type: 'text',
          group: '{{ _('Security') }}', mode: ['properties'], disabled: true
        },{
          id: 'description', label:'{{ _('Comment') }}', cell: 'string',
          type: 'multiline'
        },{
          id: 'spcoptions', label: '{{ _('Parameters') }}', type: 'collection',
          group: "Parameters", control: 'variable-collection',
          model: pgBrowser.Node.VariableModel,
          mode: ['edit', 'create'], canAdd: true, canEdit: false,
          canDelete: true
         },{
          id: 'spcacl', label: '{{ _('Privileges') }}', type: 'collection',
          group: '{{ _('Security') }}', control: 'unique-col-collection',
          model: pgBrowser.Node.PrivilegeRoleModel.extend({privileges: ['C']}),
          mode: ['edit', 'create'], canAdd: true, canDelete: true,
          uniqueCol : ['grantee'],
          columns: ['grantee', 'grantor', 'privileges']
         },{
          id: 'seclabels', label: '{{ _('Security Labels') }}',
          model: pgBrowser.SecLabelModel, editable: false, type: 'collection',
          group: '{{ _('Security') }}', mode: ['edit', 'create'],
          min_version: 90200, canAdd: true,
          canEdit: false, canDelete: true, control: 'unique-col-collection'
        }
        ],
        validate: function() {
          var err = {},
            errmsg = null,
            changedAttrs = this.sessAttrs,
            msg = undefined;
          if (_.isUndefined(this.get('name'))
              || String(this.get('name')).replace(/^\s+|\s+$/g, '') == '') {
            msg = '{{ _('Name cannot be empty.') }}';
            this.errorModel.set('name', msg);
          } else if (_.isUndefined(this.get('spclocation'))
              || String(this.get('spclocation')).replace(/^\s+|\s+$/g, '') == '') {
            msg = '{{ _('Location cannot be empty.') }}';
            this.errorModel.set('spclocation', msg);
          } else {
            this.errorModel.unset('name');
            this.errorModel.unset('spclocation');
          }
          return null;
        }
      })
  });

  }

  return pgBrowser.Nodes['coll-tablespace'];
});
