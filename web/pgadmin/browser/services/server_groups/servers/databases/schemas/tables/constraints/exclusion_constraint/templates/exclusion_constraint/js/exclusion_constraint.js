define(
        ['jquery', 'underscore', 'underscore.string', 'pgadmin',
        'pgadmin.browser', 'alertify', 'pgadmin.browser.collection'],
function($, _, S, pgAdmin, pgBrowser, Alertify) {

  var ExclusionConstraintColumnModel = pgBrowser.Node.Model.extend({
    defaults: {
      column: undefined,
      oper_class: undefined,
      order: undefined,
      nulls_order: undefined,
      operator:undefined,
      col_type:undefined
    },
    toJSON: function () {
      var d = pgBrowser.Node.Model.prototype.toJSON.apply(this, arguments);
      delete d.col_type;
      return d;
    },
    schema: [{
        id: 'column', label:'{{ _('Column') }}', type:'text', editable: false,
        cell:'string'
      },{
        id: 'oper_class', label:'{{ _('Operator class') }}', type:'text',
        node: 'table', url: 'get_oper_class', first_empty: true,
        editable: function(m) {
          if (m instanceof Backbone.Collection) {
            return true;
          }
          if ((_.has(m.collection, 'handler') &&
                !_.isUndefined(m.collection.handler) &&
                !_.isUndefined(m.collection.handler.get('oid')))) {
            return false;
          }

          if (m.collection) {
            var indexType = m.collection.handler.get('amname')
            return (indexType == 'btree' || _.isUndefined(indexType) ||
              _.isNull(indexType) || indexType == '');
          } else {
            return true;
          }
        },
        select2: {
          allowClear: true, width: 'style',
          placeholder: '{{ _("Select the operator class") }}'
        }, cell: Backgrid.Extension.Select2Cell.extend({
          initialize: function () {
            Backgrid.Extension.Select2Cell.prototype.initialize.apply(this, arguments);

          var self = this,
            url = self.column.get('url') || self.defaults.url,
            m = self.model,
            indextype = self.model.collection.handler.get('amname');

            if (url && (indextype == 'btree' || _.isUndefined(indextype) ||
                _.isNull(indextype) || indextype == '')) {
              var node = this.column.get('schema_node'),
                  eventHandler = m.top || m,
                  node_info = this.column.get('node_info'),
                  full_url = node.generate_url.apply(
                    node, [
                      null, url, this.column.get('node_data'),
                      this.column.get('url_with_id') || false, node_info
                    ]),
                  data = [];

              indextype = 'btree';

              if (this.column.get('version_compatible')) {
                eventHandler.trigger('pgadmin:view:fetching', m, self.column);
                $.ajax({
                  async: false,
                  data : {indextype:indextype},
                  url: full_url,
                  success: function(res) {
                    data = res.data;
                  },
                  error: function() {
                    eventHandler.trigger('pgadmin:view:fetch:error', m, self.column);
                  }
                });
                eventHandler.trigger('pgadmin:view:fetched', m, self.column);
              }
              /*
               * Transform the data
               */
              transform = self.column.get('transform') || self.defaults.transform;
              if (transform && _.isFunction(transform)) {
                // We will transform the data later, when rendering.
                // It will allow us to generate different data based on the
                // dependencies.
                self.column.set('options', transform.bind(self, data));
              } else {
                self.column.set('options', data);
              }
            } else {
              self.column.set('options', []);
            }
          }
        })
      },{
        id: 'order', label:'{{ _('DESC') }}', type: 'switch',
        options: {
          onText: 'ASC',
          offText: 'DESC',
        },editable: function(m) {
          if (m instanceof Backbone.Collection) {
            return true;
          }
          if ((_.has(m.collection, 'handler') &&
                !_.isUndefined(m.collection.handler) &&
                !_.isUndefined(m.collection.handler.get('oid')))) {
            return false;
          }
          return true;
        }
      },{
        id: 'nulls_order', label:'{{ _('NULLs order') }}', type:"switch",
        options: {
          onText: 'FIRST',
          offText: 'LAST',
        },editable: function(m) {
          if (m instanceof Backbone.Collection) {
            return true;
          }
          if ((_.has(m.collection, 'handler') &&
                !_.isUndefined(m.collection.handler) &&
                !_.isUndefined(m.collection.handler.get('oid')))) {
            return false;
          }
          return true;
        }
      },{
        id: 'operator', label:'{{ _('Operator') }}', type: 'text',
        node: 'table', url: 'get_operator',
        editable: function(m) {
          if (m instanceof Backbone.Collection) {
            return true;
          }
          if ((_.has(m.collection, 'handler') &&
                !_.isUndefined(m.collection.handler) &&
                !_.isUndefined(m.collection.handler.get('oid')))) {
            return false;
          }
          return true;
        },
        select2: {
          allowClear: false, width: 'style',
        }, cell: Backgrid.Extension.Select2Cell.extend({
        initialize: function () {
          Backgrid.Extension.Select2Cell.prototype.initialize.apply(this, arguments);

          var self = this,
            url = self.column.get('url') || self.defaults.url,
            m = self.model,
            col_type = self.model.get('col_type');

            self.column.set('options', []);

            if (url && !_.isUndefined(col_type) && !_.isNull(col_type) && col_type != '') {
              var node = this.column.get('schema_node'),
                  eventHandler = m.top || m,
                  node_info = this.column.get('node_info'),
                  full_url = node.generate_url.apply(
                    node, [
                      null, url, this.column.get('node_data'),
                      this.column.get('url_with_id') || false, node_info
                    ]),
                  data = [];

              if (this.column.get('version_compatible')) {
                eventHandler.trigger('pgadmin:view:fetching', m, self.column);
                $.ajax({
                  async: false,
                  data : {col_type:col_type},
                  url: full_url,
                  success: function(res) {
                    data = res.data;
                  },
                  error: function() {
                    eventHandler.trigger('pgadmin:view:fetch:error', m, self.column);
                  }
                });
                eventHandler.trigger('pgadmin:view:fetched', m, self.column);
              }
              /*
               * Transform the data
               */
              transform = self.column.get('transform') || self.defaults.transform;
              if (transform && _.isFunction(transform)) {
                // We will transform the data later, when rendering.
                // It will allow us to generate different data based on the
                // dependencies.
                self.column.set('options', transform.bind(self, data));
              } else {
                self.column.set('options', data);
              }
            }
          }
        })
      }
    ],
    validate: function() {
      this.errorModel.clear();
      var operator = this.get('operator'),
        column_name = this.get('column');
      if (_.isUndefined(operator) || _.isNull(operator)) {
        var msg = '{{ _('Please specify operator for column: ') }}' + column_name;
        this.errorModel.set('operator', msg);
        return msg;
      }
      return null;
    }
  });

  var ExclusionConstraintColumnControl =  Backform.ExclusionConstraintColumnControl =
    Backform.UniqueColCollectionControl.extend({

    initialize: function(opts) {
      Backform.UniqueColCollectionControl.prototype.initialize.apply(
        this, arguments
          );

      var self = this,
        node = 'exclusion_constraint',
        headerSchema = [{
          id: 'column', label:'', type:'text',
          node: 'column', control: Backform.NodeListByNameControl.extend({
            initialize: function() {
              // Here we will decide if we need to call URL
              // Or fetch the data from parent columns collection
                if(self.model.handler) {
                  Backform.Select2Control.prototype.initialize.apply(this, arguments);
                  // Do not listen for any event(s) for existing constraint.
                  if (_.isUndefined(self.model.get('oid'))) {
                    var tableCols = self.model.top.get('columns');
                    this.listenTo(tableCols, 'remove' , this.removeColumn);
                    this.listenTo(tableCols, 'change:name', this.resetColOptions);
                    this.listenTo(tableCols, 'change:cltype', this.resetColOptions);
                  }
                  this.custom_options();
                } else {
                  Backform.NodeListByNameControl.prototype.initialize.apply(this, arguments);
                }
            },
            removeColumn: function (m) {
              var that = this;
              setTimeout(function   () {
                that.custom_options();
                that.render.apply(that);
              }, 50);
            },
            resetColOptions: function(m) {
              var that = this;

              if (m.previous('name') ==  self.headerData.get('column')) {
                /*
                 * Table column name has changed so update
                 * column name in exclusion constraint as well.
                 */
                self.headerData.set(
                  {"column": m.get('name')});
                  self.headerDataChanged();
              }

              setTimeout(function () {
                that.custom_options();
                that.render.apply(that);
              }, 50);
            },
            custom_options: function() {
              // We will add all the columns entered by user in table model
              var columns = self.model.top.get('columns'),
                  added_columns_from_tables = [],
                  col_types = [];

              if (columns.length > 0) {
                _.each(columns.models, function(m) {
                  var col = m.get('name');
                  if(!_.isUndefined(col) && !_.isNull(col)) {
                    added_columns_from_tables.push({
                      label: col, value: col, image:'icon-column'
                      });
                    col_types.push({name:col, type:m.get('cltype')});
                  }
                });
              }
              // Set the values in to options so that user can select
              this.field.set('options', added_columns_from_tables);
              self.field.set('col_types', col_types);
            },
            remove: function () {
              if(self.model.handler) {
                  tableCols = self.model.top.get('columns');
                  this.stopListening(tableCols, 'remove' , this.removeColumn);
                  this.stopListening(tableCols, 'change:name' , this.resetColOptions);
                  this.stopListening(tableCols, 'change:cltype' , this.resetColOptions);

                Backform.Select2Control.prototype.remove.apply(this, arguments);

              } else {
                Backform.NodeListByNameControl.prototype.remove.apply(this, arguments);
              }
            },
            template: _.template([
              '<div class="<%=Backform.controlsClassName%> <%=extraClasses.join(\' \')%>">',
              '  <select class="pgadmin-node-select form-control" name="<%=name%>" style="width:100%;" value="<%-value%>" <%=disabled ? "disabled" : ""%> <%=required ? "required" : ""%> >',
              '    <% if (first_empty) { %>',
              '    <option value="" <%="" === rawValue ? "selected" : "" %>><%- empty_value %></option>',
              '    <% } %>',
              '    <% for (var i=0; i < options.length; i++) { %>',
              '    <% var option = options[i]; %>',
              '    <option <% if (option.image) { %> data-image=<%= option.image %> <% } %> value=<%= formatter.fromRaw(option.value) %> <%=option.value === rawValue ? "selected=\'selected\'" : "" %>><%-option.label%></option>',
              '    <% } %>',
              '  </select>',
              '</div>'].join("\n"))
          }),
          transform: function(rows) {
            // This will only get called in case of NodeListByNameControl.

            var that = this,
                node = that.field.get('schema_node'),
                res = [],
                col_types = [],
                filter = that.field.get('filter') || function() { return true; };

            filter = filter.bind(that);

            _.each(rows, function(r) {
              if (filter(r)) {
                var l = (_.isFunction(node['node_label']) ?
                      (node['node_label']).apply(node, [r, that.model, that]) :
                      r.label),
                    image = (_.isFunction(node['node_image']) ?
                      (node['node_image']).apply(
                        node, [r, that.model, that]
                        ) :
                      (node['node_image'] || ('icon-' + node.type)));
                res.push({
                  'value': r.label,
                  'image': image,
                  'label': l
                });
                col_types.push({name:r.label, type:r.datatype});
              }
            });
            self.field.set('col_types', col_types);
            return res;
          },
          canAdd: function(m) {
            return !((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          },
          select2: {
            allowClear: false, width: 'style',
            placeholder: 'Select column'
          }, first_empty: !self.model.isNew(),
          disabled: function(m) {
            return !_.isUndefined(self.model.get('oid'));
          }
        }],
        headerDefaults = {column: null},

        gridCols = ['column', 'oper_class', 'order', 'nulls_order', 'operator'];

      self.headerData = new (Backbone.Model.extend({
        defaults: headerDefaults,
        schema: headerSchema
      }))({});

      var headerGroups = Backform.generateViewSchema(
          self.field.get('node_info'), self.headerData, 'create',
          node, self.field.get('node_data')
          ),
          fields = [];

      _.each(headerGroups, function(o) {
        fields = fields.concat(o.fields);
      });

      self.headerFields = new Backform.Fields(fields);
      self.gridSchema = Backform.generateGridColumnsFromModel(
          self.field.get('node_info'), self.field.get('model'), 'edit', gridCols, self.field.get('schema_node')
          );

      self.controls = [];
      self.listenTo(self.headerData, "change", self.headerDataChanged);
      self.listenTo(self.headerData, "select2", self.headerDataChanged);
      self.listenTo(self.collection, "add", self.onAddorRemoveColumns);
      self.listenTo(self.collection, "remove", self.onAddorRemoveColumns);
    },

    generateHeader: function(data) {
      var header = [
        '<div class="subnode-header-form">',
        ' <div class="container-fluid">',
        '  <div class="row">',
        '   <div class="col-xs-4">',
        '    <label class="control-label"><%-column_label%></label>',
        '   </div>',
        '   <div class="col-xs-4" header="column"></div>',
        '   <div class="col-xs-4">',
        '     <button class="btn-sm btn-default add" <%=canAdd ? "" : "disabled=\'disabled\'"%> ><%-add_label%></buttton>',
        '   </div>',
        '  </div>',
        ' </div>',
        '</div>',].join("\n")

      _.extend(data, {
        column_label: '{{ _('Column')}}',
        add_label: '{{ _('ADD')}}'
      });

      var self = this,
          headerTmpl = _.template(header),
          $header = $(headerTmpl(data)),
          controls = this.controls;

      this.headerFields.each(function(field) {
        var control = new (field.get("control"))({
          field: field,
          model: self.headerData
        });

        $header.find('div[header="' + field.get('name') + '"]').append(
          control.render().$el
        );

        controls.push(control);
      });

      // We should not show add but in properties mode
      if (data.mode == 'properties') {
        $header.find("button.add").remove();
      }

      self.$header = $header;

      return $header;
    },

    events: _.extend(
                  {}, Backform.UniqueColCollectionControl.prototype.events,
                {'click button.add': 'addColumns'}
                ),

    showGridControl: function(data) {

      var self = this,
          titleTmpl = _.template("<div class='subnode-header'></div>"),
          $gridBody =
            $("<div class='pgadmin-control-group backgrid form-group col-xs-12 object subnode'></div>").append(
              titleTmpl({label: data.label})
            );

      $gridBody.append(self.generateHeader(data));

      var gridColumns = _.clone(this.gridSchema.columns);

      // Insert Delete Cell into Grid
      if (data.disabled == false && data.canDelete) {
          gridColumns.unshift({
            name: "pg-backform-delete", label: "",
            cell: Backgrid.Extension.DeleteCell,
            editable: false, cell_priority: -1
          });
      }

      if (self.grid) {
        self.grid.remove();
        self.grid.null;
      }
      // Initialize a new Grid instance
      var grid = self.grid = new Backgrid.Grid({
        columns: gridColumns,
        collection: self.collection,
        className: "backgrid table-bordered"
      });
      self.$grid = grid.render().$el;

      $gridBody.append(self.$grid);

      setTimeout(function() {
        self.headerData.set({
          'column': self.$header.find(
            'div[header="column"] select'
            ).val()
            }, {silent:true}
          );
      }, 10);

      // Render node grid
      return $gridBody;
    },

    headerDataChanged: function() {
      var self = this, val,
          data = this.headerData.toJSON(),
          inSelected = false,
          checkVars = ['column'];

      if (!self.$header) {
        return;
      }

      if (self.control_data.canAdd) {
        self.collection.each(function(m) {
          if (!inSelected) {
            _.each(checkVars, function(v) {
              if (!inSelected) {
                val = m.get(v);
                inSelected = ((
                  (_.isUndefined(val) || _.isNull(val)) &&
                  (_.isUndefined(data[v]) || _.isNull(data[v]))
                  ) ||
                  (val == data[v]));
              }
            });
          }
        });
      }
      else {
        inSelected = true;
      }

      self.$header.find('button.add').prop('disabled', inSelected);
    },

    addColumns: function(ev) {
      ev.preventDefault();
      var self = this,
          column = self.headerData.get('column');

      if (!column || column == '') {
        return false;
      }

      var coll = self.model.get(self.field.get('name')),
          m = new (self.field.get('model'))(
                self.headerData.toJSON(), {
                  silent: true, top: self.model.top,
                  collection: coll, handler: coll
                }),
          col_types =self.field.get('col_types') || [];

      for(var i=0; i < col_types.length; i++) {
        var col_type = col_types[i];
        if (col_type['name'] ==  m.get('column')) {
            m.set({'col_type':col_type['type']});
          break;
        }
      }

      coll.add(m);

      var idx = coll.indexOf(m);

      // idx may not be always > -1 because our UniqueColCollection may
      // remove 'm' if duplicate value found.
      if (idx > -1) {
        self.$grid.find('.new').removeClass('new');

        var newRow = self.grid.body.rows[idx].$el;

        newRow.addClass("new");
        $(newRow).pgMakeVisible('backform-tab');
      } else {
        delete m;
      }

      return false;
    },

    onAddorRemoveColumns: function() {
      var self = this;

      // Wait for collection to be updated before checking for the button to be
      // enabled, or not.
      setTimeout(function() {
          self.collection.trigger('pgadmin:columns:updated', self.collection);
        self.headerDataChanged();
      }, 10);
    },

    remove: function() {
      /*
       * Stop listening the events registered by this control.
       */
      this.stopListening(this.headerData, "change", this.headerDataChanged);
      this.listenTo(this.headerData, "select2", this.headerDataChanged);
      this.listenTo(this.collection, "remove", this.onAddorRemoveColumns);

      // Remove header controls.
      _.each(this.controls, function(controls) {
        controls.remove();
      });

      ExclusionConstraintColumnControl.__super__.remove.apply(this, arguments);

      // Remove the header model
      delete (this.headerData);

    }
  });

  // Extend the browser's node class for exclusion constraint node
  if (!pgBrowser.Nodes['exclusion_constraint']) {
    pgAdmin.Browser.Nodes['exclusion_constraint'] = pgBrowser.Node.extend({
      type: 'exclusion_constraint',
      label: '{{ _('Exclusion constraint') }}',
      collection_type: 'coll-constraints',
      sqlAlterHelp: 'ddl-alter.html',
      sqlCreateHelp: 'ddl-constraints.html',
      dialogHelp: '{{ url_for('help.static', filename='exclusion_constraint_dialog.html') }}',
      hasSQL: true,
      parent_type: 'table',
      canDrop: true,
      canDropCascade: true,
      hasDepends: true,
      hasStatistics: true,
      Init: function() {
        /* Avoid multiple registration of menus */
        if (this.initialized)
            return;

        this.initialized = true;

        pgBrowser.add_menus([{
          name: 'create_exclusion_constraint_on_coll', node: 'coll-constraints', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 4, label: '{{ _('Exclusion constraint...') }}',
          icon: 'wcTabIcon icon-exclusion_constraint', data: {action: 'create', check: true},
          enable: 'canCreate'
        }]);
      },
      is_not_valid: function(node) {
        return (node && !node.valid);
      },
      // Define the model for exclusion constraint node
      model: pgAdmin.Browser.Node.Model.extend({
        defaults: {
          name: undefined,
          oid: undefined,
          comment: undefined,
          spcname: "pg_default",
          amname: "gist",
          fillfactor: undefined,
          condeferrable: undefined,
          condeferred: undefined,
          columns: []
        },

        // Define the schema for the exclusion constraint node
        schema: [{
          id: 'name', label: '{{ _('Name') }}', type: 'text',
          mode: ['properties', 'create', 'edit'], editable: true,
        },{
          id: 'oid', label:'{{ _('OID') }}', cell: 'string',
          type: 'text' , mode: ['properties']
        },{
          id: 'comment', label:'{{ _('Comment') }}', cell: 'string',
          type: 'multiline', mode: ['properties', 'create', 'edit'],
          deps:['name'], disabled:function(m) {
            var name = m.get('name');
            if (!(name && name != '')) {
              setTimeout(function(){
              if(m.get('comment') && m.get('comment') !== '')
                 m.set('comment', null);
              },10);
              return true;
            } else {
              return false;
            }
          }
        },{
          id: 'spcname', label: '{{ _('Tablespace') }}',
          type: 'text', group: '{{ _('Definition') }}',
          control: 'node-list-by-name', node: 'tablespace',
          select2:{allowClear:false},
          filter: function(m) {
            // Don't show pg_global tablespace in selection.
            if (m.label == "pg_global") return false;
            else return true;
          }
        },{
          id: 'amname', label: '{{ _('Access method') }}',
          type: 'text', group: '{{ _('Definition') }}',
          url:"get_access_methods", node: 'table',
          control: Backform.NodeAjaxOptionsControl.extend({
            // When access method changes we need to clear columns collection
            onChange: function() {
              Backform.NodeAjaxOptionsControl.prototype.onChange.apply(this, arguments);
              var self = this,
              // current access method
              current_am = self.model.get('amname'),
              // previous access method
              previous_am = self.model.previous('amname'),
              column_collection = self.model.get('columns');

              if (column_collection.length > 0 && current_am != previous_am) {
                var msg = '{{ _('Changing access method will clear columns collection') }}';
                Alertify.confirm(msg, function (e) {
                    // User clicks Ok, lets clear collection
                    column_collection.reset();
                    setTimeout(function() {
                      column_collection.trigger('pgadmin:columns:updated', column_collection);
                    }, 10);

                  }, function() {
                    // User clicks Cancel set previous value again in combo box
                    setTimeout(function(){
                      self.model.set('amname', previous_am);
                    }, 10);
                });
              }
            }
          }),
          select2:{allowClear:true},
          disabled: function(m) {
            return ((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          }
        },{
          id: 'fillfactor', label: '{{ _('Fill factor') }}',
          type: 'int', group: '{{ _('Definition') }}', allowNull: true
        },{
          id: 'condeferrable', label: '{{ _('Deferrable?') }}',
          type: 'switch', group: '{{ _('Definition') }}', deps: ['index'],
          disabled: function(m) {
            return ((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          }
        },{
          id: 'condeferred', label: '{{ _('Deferred?') }}',
          type: 'switch', group: '{{ _('Definition') }}',
          deps: ['condeferrable'],
          disabled: function(m) {
            if((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew())) {
              return true;
            }

            // Disable if condeferred is false or unselected.
            if(m.get('condeferrable') == true) {
              return false;
            } else {
              setTimeout(function(){
                if(m.get('condeferred'))
                  m.set('condeferred', false);
              },10);
              return true;
            }
          }
        },{
          id: 'constraint', label:'{{ _('Constraint') }}', cell: 'string',
          type: 'multiline', mode: ['create', 'edit'], editable: false,
          group: '{{ _('Definition') }}', disabled: function(m) {
            return ((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          }
        },{
          id: 'columns', label: '{{ _('Columns') }}',
          type: 'collection', group: '{{ _('Columns') }}', disabled: false,
          deps:['amname'], canDelete: true, editable: false,
          canAdd: function(m) {
            // We can't update columns of existing exclusion constraint.
            return !((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          },
          control: ExclusionConstraintColumnControl,
          model: ExclusionConstraintColumnModel,
          disabled: function(m) {
            return ((_.has(m, 'handler') &&
              !_.isUndefined(m.handler) &&
              !_.isUndefined(m.get('oid'))) || (_.isFunction(m.isNew) && !m.isNew()));
          },
          cell: Backgrid.StringCell.extend({
            initialize: function() {
              Backgrid.StringCell.prototype.initialize.apply(this, arguments);
              var self = this;
              // Do not listen for any event(s) for existing constraint.
              if (_.isUndefined(self.model.get('oid'))) {
                var tableCols = self.model.top.get('columns');

                self.listenTo(tableCols, 'remove' , self.removeColumn);
                self.listenTo(tableCols, 'change:name', self.resetColOptions);
                self.listenTo(tableCols, 'change:cltype', self.removeColumnWithType);
              }

              this.model.get('columns').on('pgadmin:columns:updated', function() {
                self.render.apply(self);
              });
            },
            removeColumnWithType: function(m){
              var self = this,
                  cols = self.model.get('columns'),
                  removedCols = cols.where(
                    {col_type: m.previous('cltype')}
                    );

              cols.remove(removedCols);
              setTimeout(function () {
                self.render();
              }, 10);

              setTimeout(function () {
                constraints = self.model.top.get("exclude_constraint");
                var removed = [];
                constraints.each(function(constraint) {
                  if (constraint.get("columns").length == 0) {
                     removed.push(constraint);
                  }
                });
                constraints.remove(removed);
              },100);
            },
            removeColumn: function(m){
              var self = this,
                  removedCols = self.model.get('columns').where(
                    {column: m.get('name')}
                    );

              self.model.get('columns').remove(removedCols);
              setTimeout(function () {
                self.render();
              }, 10);

              setTimeout(function () {
                constraints = self.model.top.get("exclude_constraint");
                var removed = [];
                constraints.each(function(constraint) {
                  if (constraint.get("columns").length == 0) {
                     removed.push(constraint);
                  }
                });
                constraints.remove(removed);
              },100);
            },
            resetColOptions : function(m) {
                var self = this,
                  updatedCols = self.model.get('columns').where(
                  {"column": m.previous('name')}
                  );

                if (updatedCols.length > 0) {
                  /*
                   * Table column name has changed so update
                   * column name in foreign key as well.
                   */
                  updatedCols[0].set(
                  {"column": m.get('name')});
                }

                setTimeout(function () {
                  self.render();
                }, 10);
            },
            formatter: {
              fromRaw: function (rawValue, model) {
                return rawValue.pluck("column").toString();
              },
              toRaw: function (val, model) {
                return val;
              }
            },
            render: function() {
              return Backgrid.StringCell.prototype.render.apply(this, arguments);
            },
            remove: function() {
              var tableCols = this.model.top.get('columns'),
                  cols = this.model.get('columns');
              if (cols) {
                cols.off('pgadmin:columns:updated');
              }

              this.stopListening(tableCols, 'remove' , self.removeColumn);
              this.stopListening(tableCols, 'change:name' , self.resetColOptions);
              this.stopListening(tableCols, 'change:cltype' , self.removeColumnWithType);

              Backgrid.StringCell.prototype.remove.apply(this, arguments);
            }
          }),
        }],
        validate: function() {
          this.errorModel.clear();
          var columns = this.get('columns');
          if ((_.isUndefined(columns) || _.isNull(columns) || columns.length < 1)) {
            var msg = '{{ _('Please specify columns for exclusion constraint.') }}';
            this.errorModel.set('columns', msg);
            return msg;
          }

          return null;
        }
      }),

      canCreate: function(itemData, item, data) {
          // If check is false then , we will allow create menu
          if (data && data.check == false)
            return true;

          var t = pgBrowser.tree, i = item, d = itemData, parents = [];
          // To iterate over tree to check parent node
          while (i) {
            // If it is schema then allow user to create table
            if (_.indexOf(['schema'], d._type) > -1)
              return true;
            parents.push(d._type);
            i = t.hasParent(i) ? t.parent(i) : null;
            d = i ? t.itemData(i) : null;
          }
          // If node is under catalog then do not allow 'create' menu
          if (_.indexOf(parents, 'catalog') > -1) {
            return false;
          } else {
            return true;
          }
      }
    });
  }

  return pgBrowser.Nodes['exclusion_constraint'];
});
