define(
    ['jquery', 'underscore', 'pgadmin', 'backbone', 'pgadmin.browser', 'pgadmin.browser.node'],
function($, _, pgAdmin, Backbone) {

  if (!pgAdmin.Browser.Nodes['cluster']) {
    pgAdmin.Browser.Nodes['cluster'] = pgAdmin.Browser.Node.extend({
      parent_type: 'service',
      type: 'cluster',
      dialogHelp: '{{ url_for('help.static', filename='cluster_dialog.html') }}',
      label: '{{ _('Cluster') }}',
      width: '640px',
      height: '480px',
      Init: function() {
        /* Avoid multiple registration of menus */
        if (this.initialized)
            return;

        this.initialized = true;

        pgAdmin.Browser.add_menus([{
          name: 'create_cluster', node: 'cluster', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 1, label: '{{ _('Cluster...') }}',
          data: {'action': 'create'}, icon: 'wcTabIcon icon-cluster'
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
          },
          {
            id: 'tags', label:'Tags', type: 'text', group: null,
            mode: ['properties', 'edit', 'create']
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

        /* This is the only cluster - we can't remove it*/
        if (!s || s.length == 0) {
          return false;
        }
        return true;
      },
      callbacks: {
        // Add a cluster
        create_cluster: function() {
          var tree = pgAdmin.Browser.tree;
          var alert = alertify.prompt(
            '{{ _('Add a cluster') }}',
            '{{ _('Enter a name for the new cluster.') }}',
            function(evt, value) {
              $.post("{{ url_for('browser.index') }}cluster/obj/", { name: value })
                .done(function(data) {
                  if (data.success == 0) {
                    console.log('error here')
                    report_error(data.errormsg, data.info);
                  } else {
                    var item = {
                      id: data.data.id,
                      label: data.data.name,
                      inode: true,
                      open: false,
                      icon: 'icon-cluster'
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
        // Delete a cluster
        drop_cluster: function (item) {
          var tree = pgAdmin.Browser.tree;
          alertify.confirm(
            '{{ _('Delete cluster?') }}',
            '{{ _('Are you sure you wish to delete the cluster "{0}"?') }}'.replace('{0}', tree.getLabel(item)),
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
        // Rename a cluster
        rename_cluster: function (item) {
          var tree = pgAdmin.Browser.tree;
          alertify.prompt(
            '{{ _('Rename cluster') }}',
            '{{ _('Enter a new name for the cluster.') }}',
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

  return pgAdmin.Browser.Nodes['cluster'];
});
