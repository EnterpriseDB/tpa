// Domain Constraint Module: Collection and Node
define(
        ['jquery', 'underscore', 'underscore.string', 'pgadmin', 'pgadmin.browser', 'alertify', 'pgadmin.browser.collection'],
function($, _, S, pgAdmin, pgBrowser, alertify) {

  // Define Domain Constraint Collection Node
  if (!pgBrowser.Nodes['coll-domain_constraints']) {
    var domain_constraints = pgAdmin.Browser.Nodes['coll-domain_constraints'] =
      pgAdmin.Browser.Collection.extend({
        node: 'domain_constraints',
        label: '{{ _('Domain Constraints') }}',
        type: 'coll-domain_constraints',
        columns: ['name', 'description']
      });
  };

  // Domain Constraint Node
  if (!pgBrowser.Nodes['domain_constraints']) {
    pgAdmin.Browser.Nodes['domain_constraints'] = pgBrowser.Node.extend({
      type: 'domain_constraints',
      sqlAlterHelp: 'sql-alterdomain.html',
      sqlCreateHelp: 'sql-alterdomain.html',
      dialogHelp: '{{ url_for('help.static', filename='domain_constraint_dialog.html') }}',
      label: '{{ _('Domain Constraints') }}',
      collection_type: 'coll-domain_constraints',
      hasSQL: true,
      hasDepends: true,
      parent_type: ['domain'],
      Init: function() {
        // Avoid mulitple registration of menus
        if (this.initialized)
            return;

        this.initialized = true;

        pgBrowser.add_menus([{
          name: 'create_domain_on_coll', node: 'coll-domain_constraints', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 5, label: '{{ _('Domain Constraint...') }}',
          icon: 'wcTabIcon icon-domain_constraints', data: {action: 'create', check: true},
          enable: 'canCreate'
        },{
          name: 'create_domain_constraints', node: 'domain_constraints', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 5, label: '{{ _('Domain Constraint...') }}',
          icon: 'wcTabIcon icon-domain_constraints', data: {action: 'create', check: true},
          enable: 'canCreate'
        },{
          name: 'create_domain_constraints', node: 'domain', module: this,
          applies: ['object', 'context'], callback: 'show_obj_properties',
          category: 'create', priority: 5, label: '{{ _('Domain Constraint...') }}',
          icon: 'wcTabIcon icon-domain_constraints', data: {action: 'create', check: false},
          enable: 'canCreate'
        }
        ]);

      },
      canDrop: pgBrowser.Nodes['schema'].canChildDrop,
      model: pgAdmin.Browser.Node.Model.extend({
        defaults: {
          name: undefined,
          oid: undefined,
          description: undefined,
          consrc: undefined,
          connoinherit: undefined,
          convalidated: true
        },
        // Domain Constraint Schema
        schema: [{
          id: 'name', label: '{{ _('Name') }}', type:'text', cell:'string',
          disabled: 'isDisabled'
        },{
          id: 'oid', label:'{{ _('OID') }}', cell: 'string',
          type: 'text' , mode: ['properties']
        },{
          id: 'description', label: '{{ _('Comment') }}', type: 'multiline', cell:
          'string', mode: ['properties', 'create', 'edit'], min_version: 90500,
        },{
          id: 'consrc', label: '{{ _('Check') }}', type: 'multiline', cel:
          'string', group: '{{ _('Definition') }}', mode: ['properties',
          'create', 'edit'], disabled: function(m) { return !m.isNew(); }
        },{
          id: 'connoinherit', label: '{{ _('No inherit') }}', type:
          'switch', cell: 'boolean', group: '{{ _('Definition') }}', mode:
          ['properties', 'create', 'edit'], disabled: 'isDisabled',
          visible: false
        },{
          id: 'convalidated', label: "{{ _("Validate?") }}", type: 'switch', cell:
          'boolean', group: '{{ _('Definition') }}', min_version: 90200,
          disabled: function(m) {
          if (!m.isNew()) {
            var server = this.node_info.server;
            if (server.version < 90200) { return true;
            }
            else if(m.get('convalidated')) {
                return true;
            }
            return false;
          }
          return false;
          },
          mode: ['properties', 'create', 'edit']
        }],
        // Client Side Validation
        validate: function() {
          var err = {},
              errmsg;

          if (_.isUndefined(this.get('name')) || String(this.get('name')).replace(/^\s+|\s+$/g, '') == '') {
            err['name'] = '{{ _('Name cannot be empty.') }}';
            errmsg = errmsg || err['name'];
          }

          if (_.isUndefined(this.get('consrc')) || String(this.get('consrc')).replace(/^\s+|\s+$/g, '') == '') {
            err['consrc'] = '{{ _('Check cannot be empty.') }}';
            errmsg = errmsg || err['consrc'];
          }

          this.errorModel.clear().set(err);

          if (_.size(err)) {
            this.trigger('on-status', {msg: errmsg});
            return errmsg;
          }

          return null;

        },
        isDisabled: function(m){
          if (!m.isNew()) {
            var server = this.node_info.server;
            if (server.version < 90200)
            {
              return true;
            }
          }
          return false;
        }
      }),
  });

  }

  return pgBrowser.Nodes['domain'];
});
