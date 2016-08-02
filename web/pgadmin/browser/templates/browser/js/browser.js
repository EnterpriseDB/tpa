define('pgadmin.browser',
        ['require', 'jquery', 'underscore', 'underscore.string', 'bootstrap',
        'pgadmin', 'alertify', 'codemirror', 'codemirror/mode/sql/sql', 'wcdocker',
        'jquery.contextmenu', 'jquery.aciplugin', 'jquery.acitree',
        'pgadmin.alertifyjs', 'pgadmin.browser.messages',
        'pgadmin.browser.menu', 'pgadmin.browser.panel',
        'pgadmin.browser.error', 'pgadmin.browser.frame',
        'pgadmin.browser.node', 'pgadmin.browser.collection'

       ],
function(require, $, _, S, Bootstrap, pgAdmin, alertify, CodeMirror) {

  // Some scripts do export their object in the window only.
  // Generally the one, which do no have AMD support.
  var wcDocker = window.wcDocker;
  $ = $ || window.jQuery || window.$;
  Bootstrap = Bootstrap || window.Bootstrap;

  pgAdmin.Browser = pgAdmin.Browser || {};

  var panelEvents = {};
  panelEvents[wcDocker.EVENT.VISIBILITY_CHANGED] = function() {
    if (this.isVisible()) {
      var obj = pgAdmin.Browser,
          i   = obj.tree ? obj.tree.selected() : undefined,
          d   = i && i.length == 1 ? obj.tree.itemData(i) : undefined;

      if (d && obj.Nodes[d._type].callbacks['selected'] &&
          _.isFunction(obj.Nodes[d._type].callbacks['selected'])) {
        return obj.Nodes[d._type].callbacks['selected'].apply(
            obj.Nodes[d._type], [i, d, obj]);
      }
    }
  };

  // Extend the browser class attributes
  _.extend(pgAdmin.Browser, {
    // The base url for browser
    URL: {{ url_for('browser.index') }},
    // We do have docker of type wcDocker to take care of different
    // containers. (i.e. panels, tabs, frames, etc.)
    docker:null,
    // Reversed Engineer query for the selected database node object goes
    // here
    editor:null,
    // Left hand browser tree
    tree:null,
    // list of script to be loaded, when a certain type of node is loaded
    // It will be used to register extensions, tools, child node scripts,
    // etc.
    scripts: {},
    // Default panels
    panels: {
      // Panel to keep the left hand browser tree
      'browser': new pgAdmin.Browser.Panel({
        name: 'browser',
        title: '{{ _('Browser') }}',
        showTitle: true,
        isCloseable: false,
        isPrivate: true,
        icon: 'fa fa-binoculars',
        content: '<div id="tree" class="aciTree"></div>'
      }),
      // Properties of the object node
      'properties': new pgAdmin.Browser.Panel({
        name: 'properties',
        title: '{{ _('Properties') }}',
        icon: 'fa fa-cogs',
        width: 500,
        isCloseable: false,
        isPrivate: true,
        elContainer: true,
        content: '<div class="obj_properties"><div class="alert alert-info pg-panel-message">{{ _('Please select an object in the tree view.') }}</div></div>',
        events: panelEvents,
        onCreate: function(myPanel, $container) {
          $container.addClass('pg-no-overflow');
        }
      }),
      // Statistics of the object
      'statistics': new pgAdmin.Browser.Panel({
        name: 'statistics',
        title: '{{ _('Statistics') }}',
        icon: 'fa fa-line-chart',
        width: 500,
        isCloseable: false,
        isPrivate: true,
        content: '<div><div class="alert alert-info pg-panel-message pg-panel-statistics-message">{{ _('Please select an object in the tree view.') }}</div><div class="pg-panel-statistics-container hidden"></div></div>',
        events: panelEvents
      }),
      // Reversed engineered SQL for the object
      'sql': new pgAdmin.Browser.Panel({
        name: 'sql',
        title: '{{ _('SQL') }}',
        icon: 'fa fa-file-text-o',
        width: 500,
        isCloseable: false,
        isPrivate: true,
        content: '<textarea id="sql-textarea" name="sql-textarea"></textarea>'
      }),
      // Dependencies of the object
      'dependencies': new pgAdmin.Browser.Panel({
        name: 'dependencies',
        title: '{{ _('Dependencies') }}',
        icon: 'fa fa-hand-o-up',
        width: 500,
        isCloseable: false,
        isPrivate: true,
        content: '<div><div class="alert alert-info pg-panel-message pg-panel-depends-message">{{ _('Please select an object in the tree view.') }}</div><div class="pg-panel-depends-container hidden"></div></div>',
        events: panelEvents
      }),
      // Dependents of the object
      'dependents': new pgAdmin.Browser.Panel({
        name: 'dependents',
        title: '{{ _('Dependents') }}',
        icon: 'fa fa-hand-o-down',
        width: 500,
        isCloseable: false,
        isPrivate: true,
        content: '<div><div class="alert alert-info pg-panel-message pg-panel-depends-message">{{ _('Please select an object in the tree view.') }}</div><div class="pg-panel-depends-container hidden"></div></div>',
        events: panelEvents
      })/* Add hooked-in panels by extensions */{% for panel_item in current_app.panels %}{% if not panel_item.isIframe %},'{{ panel_item.name }}' : new pgAdmin.Browser.Panel({
        name: '{{ panel_item.name }}',
        title: '{{ panel_item.title }}',
        icon: '{{ panel_item.icon }}',
        width: {{ panel_item.width }},
        height: {{ panel_item.height }},
        showTitle: {% if panel_item.showTitle %}true{% else %}false{% endif %},
        isCloseable: {% if panel_item.isCloseable %}true{% else %}false{% endif %},
        isPrivate: {% if panel_item.isPrivate %}true{% else %}false{% endif %},
        content: '{{ panel_item.content }}'{% if panel_item.events is not none %},
        events: {{ panel_item.events }} {% endif %}
      }){% endif %}{% endfor %}
    },
    // We also support showing dashboards, HTML file, external URL
    frames: {
      /* Add hooked-in frames by extensions */{% for panel_item in current_app.panels %}{% if panel_item.isIframe %}
      '{{ panel_item.name }}' : new pgAdmin.Browser.Frame({
        name: '{{ panel_item.name }}',
        title: '{{ panel_item.title }}',
        icon: '{{ panel_item.icon }}',
        width: {{ panel_item.width }},
        height: {{ panel_item.height }},
        showTitle: {% if panel_item.showTitle %}true{% else %}false{% endif %},
        isCloseable: {% if panel_item.isCloseable %}true{% else %}false{% endif %},
        isPrivate: {% if panel_item.isPrivate %}true{% else %}false{% endif %},
        url: '{{ panel_item.content }}'
     }),{% endif %}{% endfor %}
    },
      /* Menus */
      // pgAdmin.Browser.MenuItem.add_menus(...) will register all the menus
      // in this container
    menus: {
      // All context menu goes here under certain menu types.
      // i.e. context: {'server': [...], 'server-group': [...]}
      context: {},
      // File menus
      file: {},
      // Edit menus
      edit: {},
      // Object menus
      object: {},
      // Management menus
      management: {},
      // Tools menus
      tools: {},
      // Help menus
      help: {}
    },
    menu_categories: {
      /* name, label (pair) */
      'create': {
        label: '{{ _('Create')|safe }}',
        priority: 1,
        /* separator above this menu */
        above: false,
        below: true,
        icon: 'fa fa-magic',
        single: true
      }
    },
    // A callback to load/fetch a script when a certain node is loaded
    register_script: function(n, m, p) {
      var scripts = this.scripts;
      scripts[n] = _.isArray(scripts[n]) ? scripts[n] : [];
      scripts[n].push({'name': m, 'path': p, loaded: false});
    },
    // Build the default layout
    buildDefaultLayout: function() {
      var browserPanel = this.docker.addPanel('browser', wcDocker.DOCK.LEFT);
      var dashboardPanel = this.docker.addPanel(
              'dashboard', wcDocker.DOCK.RIGHT, browserPanel);
      this.docker.addPanel('properties', wcDocker.DOCK.STACKED, dashboardPanel, {
          tabOrientation: wcDocker.TAB.TOP
      });
      this.docker.addPanel('sql', wcDocker.DOCK.STACKED, dashboardPanel);
      this.docker.addPanel(
              'statistics', wcDocker.DOCK.STACKED, dashboardPanel);
      this.docker.addPanel(
              'dependencies', wcDocker.DOCK.STACKED, dashboardPanel);
      this.docker.addPanel(
              'dependents', wcDocker.DOCK.STACKED, dashboardPanel);
    },
    // Enable/disable menu options
    enable_disable_menus: function(item) {
      // Mechanism to enable/disable menus depending on the condition.
      var obj = this, j, e,
          // menu navigation bar
          navbar = $('#navbar-menu > ul').first(),
          // Drop down menu for objects
          $obj_mnu = navbar.find('li#mnu_obj > ul.dropdown-menu').first(),
          // data for current selected object
          d = obj.tree.itemData(item),
          update_menuitem = function(m) {
            if (m instanceof pgAdmin.Browser.MenuItem) {
              m.update(d, item);
            } else {
              for (var key in m) {
                update_menuitem(m[key]);
              }
            }
          };

      // All menus from the object menus (except the create drop-down
      // menu) needs to be removed.
      $obj_mnu.empty();

      // All menus (except for the object menus) are already present.
      // They will just require to check, wheather they are
      // enabled/disabled.
      _.each([
        {m: 'cluster', id: '#mnu_cluster'},
        {m: 'file', id: '#mnu_file'},
        {m: 'edit', id: '#mnu_edit'},
        {m: 'management', id: '#mnu_management'},
        {m: 'tools', id: '#mnu_tools'},
        {m: 'help', id:'#mnu_help'}], function(o) {
          _.each(
            obj.menus[o.m],
            function(m, k) {
              update_menuitem(m);
            });
        });

      // Create the object menu dynamically
      if (item && obj.menus['object'] && obj.menus['object'][d._type]) {
        pgAdmin.Browser.MenuCreator(
          $obj_mnu, obj.menus['object'][d._type], obj.menu_categories, d, item
        )
      } else {
        // Create a dummy 'no object seleted' menu
        create_submenu = pgAdmin.Browser.MenuGroup(
          obj.menu_categories['create'], [{
            $el: $('<li class="menu-item disabled"><a href="#">{{ _("No object selected") }}</a></li>'),
            priority: 1,
            category: 'create',
            update: function() {}
          }], false);
        $obj_mnu.append(create_submenu.$el);
      }
    },
    init: function() {
      var obj=this;
      if (obj.initialized) {
        return;
      }
      obj.initialized = true;

      // Store the main browser layout
      $(window).bind('unload', function() {
          if(obj.docker) {
            state = obj.docker.save();
            settings = { setting: "Browser/Layout", value: state };
            $.ajax({
              type: 'POST',
              url: "{{ url_for('settings.store') }}",
              data: settings,
              async:false
            });
          }
        return true;
      });

      // Initialize the Docker
      obj.docker = new wcDocker(
        '#dockerContainer', {
        allowContextMenu: true,
        allowCollapse: false,
        themePath: '../static/css/wcDocker/Themes',
        theme: 'pgadmin'
      });
      if (obj.docker) {
        // Initialize all the panels
        _.each(obj.panels, function(panel, name) {
          obj.panels[name].load(obj.docker);
        });
        // Initialize all the frames
        _.each(obj.frames, function(frame, name) {
          obj.frames[name].load(obj.docker);
        });

        // Stored layout in database from the previous session
        var layout = '{{ layout }}';

        // Try to restore the layout if there is one
        if (layout != '') {
          try {
            obj.docker.restore(layout)
          }
          catch(err) {
            obj.docker.clear();
            obj.buildDefaultLayout()
          }
        } else {
          obj.buildDefaultLayout()
        }
      }

      // Syntax highlight the SQL Pane
      obj.editor = CodeMirror.fromTextArea(
          document.getElementById("sql-textarea"), {
            lineNumbers: true,
            lineWrapping: true,
            mode: "text/x-pgsql",
            readOnly: true
          });

      setTimeout(function() {
        obj.editor.refresh();
      }, 10);

      // Initialise the treeview
      $('#tree').aciTree({
        ajax: {
          url: '{{ url_for('browser.get_nodes') }}',
          converters: {
            'text json': function(payload) {
              return $.parseJSON(payload).data;
            }
          }
        },
        ajaxHook: function(item, settings) {
          if (item != null) {
            var d = this.itemData(item);
                n = obj.Nodes[d._type];
            if (n)
              settings.url = n.generate_url(item, 'children', d, true);
          }
        },
        loaderDelay: 100,
        show: {
          duration: 75
        },
        hide: {
          duration: 75
        },
        view: {
          duration: 75
        }
      });

      obj.tree = $('#tree').aciTree('api');

      // Build the treeview context menu
      $('#tree').contextMenu({
        selector: '.aciTreeLine',
        autoHide: false,
        build: function(element) {
          var item = obj.tree.itemFrom(element),
              d = obj.tree.itemData(item),
              menus = obj.menus['context'][d._type],
              $div = $('<div></div>'),
              context_menu = {};

          pgAdmin.Browser.MenuCreator(
            $div, menus, obj.menu_categories, d, item, context_menu
          );

          return {
            autoHide: false,
            items: context_menu
          };
        }
      });

      // Treeview event handler
      $('#tree').on('acitree', function(event, api, item, eventName, options) {
        var d = item ? obj.tree.itemData(item) : null;

        switch (eventName) {
          // When a node is added in the browser tree, we need to
          // load the registered scripts
          case "added":
            if (d) {
              /* Loading all the scripts registered to be loaded on this node */
              if (obj.scripts && obj.scripts[d._type]) {
                var scripts = _.extend({}, obj.scripts[d._type]);

                /*
                 * We can remove it from the Browser.scripts object as
                 * these're about to be loaded.
                 *
                 * This will make sure that we check for the script to be
                 * loaded only once.
                 *
                 */
                delete obj.scripts[d._type];

                setTimeout(function() {
                  _.each(scripts, function(s) {
                    if (!s.loaded) {
                      require([s.name], function(m) {
                        s.loaded = true;
                        // Call the initializer (if present)
                        if (m && m.init && typeof m.init == 'function') {
                          try {
                            m.init();
                            obj.Events.trigger(
                              'pgadmin-browser:' + s.name + ':initialized', m, obj
                            );
                          } catch (err) {
                            console.log("Error running module init script for '" + s.path + "'");
                            console.log(err);

                            obj.report_error(
                              '{{ _('Error Initializing script - ') }}' + s.path, err);
                          }
                        }
                      }, function() {
                        console.log("Error loading script - " + s.path);
                        console.log(arguments);
                        obj.report_error(
                          '{{ _('Error loading script - ') }}' + s.path);
                      }).bind(s);
                    }
                  });
                }, 1);
              }
            }
            break;
        }

        var node;

        if (d && obj.Nodes[d._type]) {
          node = obj.Nodes[d._type];

          /* If the node specific callback returns false, we will also return
           * false for further processing.
           */
          if (_.isObject(node.callbacks) &&
              eventName in node.callbacks &&
              typeof node.callbacks[eventName] == 'function' &&
              !node.callbacks[eventName].apply(
                  node, [item, d, obj, options, eventName])) {
            return false;
          }
          /* Raise tree events for the nodes */
          try {
            node.trigger(
                'browser-node.' + eventName, node, item, d
                );
          } catch (e) {
            console.log(e);
          }
        }

        try {
            console.log("Event "+ JSON.stringify(eventName));
            console.log("item "+ JSON.stringify(item));
            console.log("d "+ JSON.stringify(d));
            console.log("Node "+ JSON.stringify(node));
          obj.Events.trigger(
              'pgadmin-browser:tree', eventName, item, d
              );
          obj.Events.trigger(
              'pgadmin-browser:tree:' + eventName, item, d, node
              );
        } catch (e) {
          console.log(e);
        }
        return true;
      });

      // There are some scripts which needed to be loaded immediately,
      // but - not all. We will will need to generate all the menus only
      // after they all were loaded completely.
      var counter = {total: 0, loaded: 0};
      {% for script in current_app.javascripts %}{% if 'when' in script %}
      {% if script.when %}/* Registering '{{ script.path }}.js' to be loaded when a node '{{ script.when }}' is loaded */
      this.register_script('{{ script.when }}', '{{ script.name }}', '{{ script.path }}.js');{% else %}/* Loading '{{ script.path }}' */
      counter.total += 1;
      this.load_module('{{ script.name }}', '{{ script.path }}', counter);{% endif %}{% endif %}{% endfor %}

      var geneate_menus = function() {
        // Generate the menu items only when all the initial scripts
        // were loaded completely.
        //
        // First - register the menus from the other
        // modules/extensions.
        if (counter.total == counter.loaded) {
{% for key in ('File', 'Edit', 'Object' 'Tools', 'Management', 'Help') %}{% set menu_items = current_app.menu_items['%s_items' % key.lower()] %}{% if menu_items|length > 0 %}{% set hasMenus = False %}
          obj.add_menus([{% for item in menu_items %}{% if hasMenus %},{% endif %}{
            name: "{{ item.name }}",
            {% if item.module %}module: {{ item.module }},
            {% endif %}{% if item.url %}url: "{{ item.url }}",
            {% endif %}{% if item.target %}target: "{{ item.target }}",
            {% endif %}{% if item.callback %}callback: "{{ item.callback }}",
            {% endif %}{% if item.category %}category: "{{ item.category }}",
            {% endif %}{% if item.icon %}icon: '{{ item.icon }}',
            {% endif %}{% if item.data %}data: {{ item.data }},
            {% endif %}label: '{{ item.label }}', applies: ['{{ key.lower() }}'],
            priority: {{ item.priority }},
            enable: '{{ item.enable }}'
          }{% set hasMenus = True %}{% endfor %}]);
{% endif %}{% endfor %}
          obj.create_menus();
        } else {
          // recall after some time
          setTimeout(function() { geneate_menus(); }, 300);
        }
      };
      geneate_menus();

      // Ping the server every 5 minutes
      setInterval(function() {
        $.ajax({
          url: '{{ url_for('misc.ping') }}',
          type:'POST',
          success: function() {},
          error: function() {}
          });
        }, 300000);
    },
    // load the module right now
    load_module: function(name, path, c) {
      var obj = this;
      require([name],function(m) {
        try {
          // initialze the module (if 'init' function present).
          if (m.init && typeof(m.init) == 'function')
            m.init();
        } catch (e) {
          // Log this exception on console to understand the issue properly.
          console.log(e);
          obj.report_error(
            '{{ _('Error loading script - ') }}' + path);
        }
        if (c)
        c.loaded += 1;
      }, function() {
        // Log the arguments on console to understand the issue properly.
        console.log(arguments);
        obj.report_error(
          '{{ _('Error loading script - ') }}' + path);
      });
    },
    add_menu_category: function(
      id, label, priority, icon, above_separator, below_separator, single
    ) {
      this.menu_categories[id] = {
        label: label,
        priority: priority,
        icon: icon,
        above: (above_separator === true),
        below: (below_separator === true),
        single: single
      }
    },
    // Add menus of module/extension at appropriate menu
    add_menus: function(menus) {
      var pgMenu = this.menus;
      var MenuItem = pgAdmin.Browser.MenuItem;
      _.each(menus, function(m) {
        _.each(m.applies, function(a) {
          /* We do support menu type only from this list */
          if ($.inArray(a, [
              'context', 'file', 'edit', 'object',
              'management', 'tools', 'help']) >= 0) {
            var menus;
            pgMenu[a] = pgMenu[a] || {};
            if (_.isString(m.node)) {
              menus = pgMenu[a][m.node] = pgMenu[a][m.node] || {};
            } else if (_.isString(m.category)) {
              menus = pgMenu[a][m.category] = pgMenu[a][m.category] || {};
            }
            else {
              menus = pgMenu[a];
            }

            if (_.has(menus, m.name)) {
              console && console.log && console.log(m.name +
                ' has been ignored!\nIt already exists in the ' +
                a +
                ' list of menus!');
            } else {
              menus[m.name] = new MenuItem({
                name: m.name, label: m.label, module: m.module,
                category: m.category, callback: m.callback,
                priority: m.priority, data: m.data, url: m.url,
                target: m.target, icon: m.icon,
                enable: (m.enable == '' ? true : (_.isString(m.enable) &&
                   m.enable.toLowerCase() == 'false') ?
                  false : m.enable),
                node: m.node
              });
            }
          } else  {
            console && console.log &&
              console.log(
                  "Developer warning: Category '" +
                  a +
                  "' is not supported!\nSupported categories are: context, file, edit, object, tools, management, help");
          }
        });
      });
    },
    // Create the menus
    create_menus: function() {

      /* Create menus */
      var navbar = $('#navbar-menu > ul').first();
      var obj = this;

      _.each([
        {menu: 'cluster', id: '#mnu_cluster'},
        {menu: 'file', id: '#mnu_file'},
        {menu: 'edit', id: '#mnu_edit'},
        {menu: 'management', id: '#mnu_management'},
        {menu: 'tools', id: '#mnu_tools'},
        {menu: 'help', id:'#mnu_help'}],
        function(o) {
          var $mnu = navbar.children(o.id).first(),
              $dropdown = $mnu.children('.dropdown-menu').first();
          $dropdown.empty();
          var menus = {};

          if (pgAdmin.Browser.MenuCreator(
            $dropdown, obj.menus[o.menu], obj.menu_categories
            )) {
            $mnu.removeClass('hide');
          }
        });

      navbar.children('#mnu_obj').removeClass('hide');
       obj.enable_disable_menus();
    },
    // General function to handle callbacks for object or dialog help.
    showHelp: function(type, url, node, item, label) {
      if (type == "object_help") {
        // See if we can find an existing panel, if not, create one
        pnlSqlHelp = this.docker.findPanels('pnl_sql_help')[0];

        if (pnlSqlHelp == null) {
          pnlProperties = this.docker.findPanels('properties')[0];
          this.docker.addPanel('pnl_sql_help', wcDocker.DOCK.STACKED, pnlProperties);
          pnlSqlHelp = this.docker.findPanels('pnl_sql_help')[0];
        }

        // Construct the URL
        server = node.getTreeNodeHierarchy(item).server;

        baseUrl = '{{ pg_help_path }}'
        if (server.server_type == 'ppas') {
          baseUrl = '{{ edbas_help_path }}'
        }

        major = Math.floor(server.version / 10000)
        minor = Math.floor(server.version / 100) - (major * 100)

        baseUrl = baseUrl.replace('$VERSION$', major + '.' + minor)
        if (!S(baseUrl).endsWith('/')) {
          baseUrl = baseUrl + '/'
        }
        fullUrl = baseUrl+ url;
        // Update the panel
        iframe = $(pnlSqlHelp).data('embeddedFrame');
        pnlSqlHelp.title('Help: '+ label);

        pnlSqlHelp.focus();
        iframe.openURL(fullUrl);
      } else if(type == "dialog_help") {
        // See if we can find an existing panel, if not, create one
        pnlDialogHelp = this.docker.findPanels('pnl_online_help')[0];

        if (pnlDialogHelp == null) {
          pnlProperties = this.docker.findPanels('properties')[0];
          this.docker.addPanel('pnl_online_help', wcDocker.DOCK.STACKED, pnlProperties);
          pnlDialogHelp = this.docker.findPanels('pnl_online_help')[0];
        }

        // Update the panel
        iframe = $(pnlDialogHelp).data('embeddedFrame');

        pnlDialogHelp.focus();
        iframe.openURL(url);
      }
    }
  });

  window.onbeforeunload = function(ev) {
    var e = ev || window.event,
        msg = '{{ _('Do you really want to leave the page?') }}';

    // For IE and Firefox prior to version 4
    if (e) {
      e.returnValue = msg;
    }

    // For Safari
    return msg;
  };

  return pgAdmin.Browser;
});
