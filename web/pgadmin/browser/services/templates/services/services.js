define(
    ['jquery', 'underscore', 'pgadmin', 'backbone', 'pgadmin.browser', 'pgadmin.browser.node'],
function($, _, pgAdmin, Backbone) {

  if (!pgAdmin.Browser.Nodes['service']) {
    pgAdmin.Browser.Nodes['service'] = pgAdmin.Browser.Node.extend({
      parent_type: null,
      type: 'service',
      dialogHelp: '{{ url_for('help.static', filename='service_dialog.html') }}',
      label: '{{ _('Service') }}',
      width: '800px',
      height: '540px',
      Init: function() {
        /* Avoid multiple registration of menus */
        if (this.initialized)
            return;

        this.initialized = true;

        pgAdmin.Browser.add_menus([{
          name: 'create_service', node: 'service', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 1, label: '{{ _('Service...') }}',
          data: {'action': 'create'}, icon: 'wcTabIcon icon-service'
        },{
            name: 'provisioning_status', node: 'service', 'module': this,
            applies: ['object', 'context'], callback: 'provisioning_status',
            category: 'status', priority: 2, label: '{{ _('Provisioning status...') }}',
            data: {'action': 'status'}, icon: 'wcTabIcon icon-service'
        }]);
      },
      model: pgAdmin.Browser.Node.Model.extend({
        defaults: {
          id: undefined,
          name: null
        },
        schema: [
          {
            id: 'id', label: 'ID', type: 'int', group: null,
            mode: ['properties']
          },{
            id: 'name', label:'Name', type: 'text', group: null,
            mode: ['properties', 'edit', 'create']
          },{
            id: 'server_software', label:'Server Software', type: 'options', group: null,
            mode: ['properties', 'edit', 'create'],
            'options': [{% for ss in metadata %}
            {label: '{{ ss.name }}', value: '{{ ss.id }}'},{% endfor %}
            {label: '----Select----', value:0 },
            //{label: 'PostgreSQL 9.4', value:1 },
            {label: 'PostgreSQL 9.5', value:2, },
            {label: 'PostgreSQL 9.6', value:3 },
            //{label: '2ndQuadrant PostgreSQL 9.4', value:4 },
            {label: '2ndQuadrant PostgreSQL 9.5', value:5 },
            //{label: '2ndQuadrant PostgreSQL 9.6', value:6 },
            //{label: 'Postgres-XL 9.5', value:7 },
            {label: '2ndQuadrant Postgres-XL 9.5', value:8 },
            {label: '2ndQuadrant BDR 9.5 v1.0', value:9 }
          ]
          },{
            id: 'plan', label:'Plan', type: 'options', group: null,
            mode: ['properties', 'edit', 'create'],
            'options': [{% for ss in metadata %}
            {label: '{{ ss.name }}', value: '{{ ss.id }}'},{% endfor %}
            {label: '----Select----', value:0 },
            {label: 'AWS t2.nano', value:1 },
            {label: 'AWS t2.micro', value:2 },
            {label: 'AWS t2.small', value:3 },
            {label: 'AWS t2.medium', value:4 },
            {label: 'AWS t2.large', value:5 },
            {label: 'AWS m4.large', value:6 },
            {label: 'AWS m4.xlarge', value:7 },
            {label: 'AWS m4.2xlarge', value:8 },
            {label: 'AWS m4.4xlarge', value:9 },
            {label: 'AWS m3.medium', value:10 },
            {label: 'AWS m3.large', value:11},
            {label: 'AWS m3.xlarge', value:12 },
            {label: 'AWS m3.2xlarge', value:13 },
          ]
          },{
            id: 'config_type', label:'Configuration', type: 'radio', group: "{{ 'Configuration' }}",
            mode: ['properties', 'edit', 'create'],
            'options':[{label: 'Basic', value:1, extraClasses:['col-sm-2'], 
                        img_src:'{{ url_for('static', filename='img/config_basic.png') }}'},
            {label: 'Basic + Dedicated Barman', value:2, extraClasses:['col-sm-2'],
                        img_src:'{{ url_for('static', filename='img/config_barman_dedicated.jpg') }}'},
            {label: 'Basic + Shared Barman', value:3, extraClasses:['col-sm-2'],
                        img_src:'{{ url_for('static', filename='img/config_barman_shared.jpg') }}' },
            {label: 'Postgres-XL', value:4, extraClasses:['col-sm-2'],
                        img_src:'{{ url_for('static', filename='img/config_xl.jpg') }}'},
            {label: 'BDR', value:5, extraClasses:['col-sm-2'],
                        img_src:'{{ url_for('static', filename='img/config_bdr.jpg') }}' }]
          },
          {
            id: 'backup_start', label:'Backup Start Time', type: 'text', group: "{{ 'Backup' }}",
            mode: ['properties', 'edit', 'create']
          },{
            id: 'backup_frequency', label:'Backup Frequency', type: 'options', group: "{{ 'Backup' }}",
            mode: ['properties', 'edit', 'create'],
            'options': [{% for ss in metadata %}
            {label: '{{ ss.name }}', value: '{{ ss.id }}'},{% endfor %}
            {label: 'Daily', value:1 },
            {label: 'Weekly, Monday', value:2 },
            {label: 'Weekly, Tuesday', value:3 },
            {label: 'Weekly, Wednesday', value:4 },
            {label: 'Weekly, Thursday', value:5 },
            {label: 'Weekly, Friday', value:6 },
            {label: 'Weekly, Saturday', value:7 },
            {label: 'Weekly, Sunday', value:8 }
          ]
          }
        ],
        validate: function(attrs, options) {
          if (!this.isNew() && 'id' in this.changed) {
            return '{{ _('The ID cannot be changed.') }}';
          }
          if (String(this.name).replace(/^\s+|\s+$/g, '') == '') {
            return '{{ _('Name cannot be empty.') }}';
          }
          return null;
        }
      }),
      canDrop: function(itemData, item, data) {
        if(itemData.can_delete) {
          return true;
        }
        return false;
      },
      canDelete: function(i) {
        var s = pgAdmin.Browser.tree.siblings(i, true);

        /* This is the only service - we can't remove it*/
        if (!s || s.length == 0) {
          return false;
        }
        return true;
      },
      callbacks: {
        // Add a service
        create_service: function() {

          var tree = pgAdmin.Browser.tree;
          var alert = alertify.prompt(
            '{{ _('Add a service') }}',
            '{{ _('Enter a name for the new service.') }}',
            function(evt, value) {
              $.post("{{ url_for('browser.index') }}service/obj/", { name: value })
                .done(function(data) {
                  if (data.success == 0) {
                    report_error(data.errormsg, data.info);
                  } else {
                    var item = {
                      id: data.data.id,
                      label: data.data.name,
                      inode: true,
                      open: false,
                      icon: 'icon-service'
                    }
                    tree.append(null, {
                      itemData: item
                    });
                  }
                })
            },
            function() {}
          );
          alert.show();
        },

        // Delete a service
        drop_service: function (item) {
          var tree = pgAdmin.Browser.tree;
          alertify.confirm(
            '{{ _('Delete service?') }}',
            '{{ _('Are you sure you wish to delete the service "{0}"?') }}'.replace('{0}', tree.getLabel(item)),
            function() {
              var d = tree.itemData(item);
              $.ajax({
                url:"{{ url_for('browser.index') }}" + d._type + "/obj/" + d.refid,
                type:'DELETE',
                success: function(data) {
                  if (data.success == 0) {
                    report_error(data.errormsg, data.info);
                  } else {
                    var next = tree.next(item);
                    var prev = tree.prev(item);
                    tree.remove(item);
                    if (next.length) {
                      tree.select(next);
                    } else if (prev.length) {
                      tree.select(prev);
                    }
                  }
                }
              });
            },
            function() {}
          ).show();
        },

        // Rename a service
        rename_service: function (item) {
          var tree = pgAdmin.Browser.tree;
          alertify.prompt(
            '{{ _('Rename service') }}',
            '{{ _('Enter a new name for the service.') }}',
            tree.getLabel(item),
            function(evt, value) {
              var d = tree.itemData(item);
              $.ajax({
                url:"{{ url_for('browser.index') }}" + d._type + "/obj/" + d.refid,
                type:'PUT',
                params: { name: value },
                success: function(data) {
                  if (data.success == 0) {
                    report_error(data.errormsg, data.info);
                  } else {
                    tree.setLabel(item, { label: value });
                  }
                }
              })
            },
            null
          ).show();
        }
      }
    });
  }
  $("#server_software").change(function() {
             var str = "";
             $( "select option:selected" ).each(function() {
                 str += $( this ).text() + "";
             });
        }).change();

  return pgAdmin.Browser.Nodes['service'];
});

