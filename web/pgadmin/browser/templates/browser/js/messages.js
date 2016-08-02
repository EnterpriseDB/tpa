define('pgadmin.browser.messages',
        ['underscore', 'underscore.string', 'pgadmin'],
function(_, S, pgAdmin) {

  var pgBrowser = pgAdmin.Browser = pgAdmin.Browser || {};

  if (pgBrowser.messages)
    return pgBrowser.messages;

  var messages = pgBrowser.messages = {
    'SERVER_LOST': '{{ _('Connection to the server has been lost.') }}',
    'CLICK_FOR_DETAILED_MSG': '{{ _('Click here for details.')|safe }}',
    'GENERAL_CATEGORY': '{{ _("General")|safe }}',
    'SQL_TAB': '{{ _('SQL') }}',
    'SQL_INCOMPLETE': '{{ _('Incomplete definition') }}',
    'SQL_NO_CHANGE': '-- ' + '{{ _('Nothing changed')|safe }}',
    'MUST_BE_INT' : "{{ _("'%%s' must be an integer.")|safe }}",
    'MUST_BE_NUM' : "{{ _("'%%s' must be a numeric.")|safe }}",
    'MUST_GR_EQ' : "{{ _("'%%s' must be greater than or equal to %%d.")|safe }}",
    'MUST_LESS_EQ' : "{{ _("'%%s' must be less than or equal to %%d.")|safe }}",
    'STATISTICS_LABEL': "{{ _("Statistics") }}",
    'STATISTICS_VALUE_LABEL': "{{ _("Value") }}",
    'NODE_HAS_NO_SQL': "{{ _("No SQL could be generated for the selected object.") }}",
    'NODE_HAS_NO_STATISTICS': "{{ _("No statistics are available for the selected object.") }}",
    'TRUE': "{{ _("True") }}",
    'FALSE': "{{ _("False") }}",
    'NOTE_CTRL_LABEL': "{{ _("Note") }}"
  };

{% for key in current_app.messages.keys() %}
  messages['{{ key|safe }}'] = '{{ current_app.messages[key]|safe }}';

{% endfor %}

  return pgBrowser.messages;

});
