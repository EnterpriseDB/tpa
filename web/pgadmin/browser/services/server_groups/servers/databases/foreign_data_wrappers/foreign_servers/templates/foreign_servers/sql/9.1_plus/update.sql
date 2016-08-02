{% import 'macros/privilege.macros' as PRIVILEGE %}
{% if data %}
{# ============= Update foreign server name ============= #}
{% if data.name != o_data.name %}
ALTER SERVER {{ conn|qtIdent(o_data.name) }}
    RENAME TO {{ conn|qtIdent(data.name) }};

{% endif %}
{# ============= Update foreign server owner ============= #}
{% if data.fsrvowner and data.fsrvowner != o_data.fsrvowner %}
ALTER SERVER {{ conn|qtIdent(data.name) }}
    OWNER TO {{ conn|qtIdent(data.fsrvowner) }};

{% endif %}
{# ============= Update foreign server version ============= #}
{% if data.fsrvversion and data.fsrvversion != o_data.fsrvversion %}
ALTER SERVER {{ conn|qtIdent(data.name) }}
    VERSION {{ data.fsrvversion|qtLiteral }};

{% endif %}
{# ============= Update foreign server comments ============= #}
{% if data.description is defined and data.description != o_data.description %}
COMMENT ON SERVER {{ conn|qtIdent(data.name) }}
    IS {{ data.description|qtLiteral }};

{% endif %}
{# ============= Update foreign server options and values ============= #}
{% if data.fsrvoptions and data.fsrvoptions.deleted %}
{% set addAlter = "False" %}
{% for variable in data.fsrvoptions.deleted %}
{% if variable.fsrvoption and variable.fsrvoption != '' %}
{% if addAlter == "False" %}
ALTER SERVER {{ conn|qtIdent(data.name) }}
    OPTIONS ({% set addAlter = "True" %}{%endif%}
DROP {{conn|qtIdent(variable.fsrvoption)}}{% if not loop.last %},{% else %});{% endif %}
{% endif %}
{% endfor %}


{% endif %}
{% if data.fsrvoptions and data.fsrvoptions.added %}
{% set addAlter = "False" %}
{% for variable in data.fsrvoptions.added %}
{% if variable.fsrvoption and variable.fsrvoption != '' %}
{% if addAlter == "False" %}
ALTER SERVER {{ conn|qtIdent(data.name) }}
    OPTIONS ({% set addAlter = "True" %}{%endif%}
ADD {{ conn|qtIdent(variable.fsrvoption) }} {{variable.fsrvvalue|qtLiteral}}{% if not loop.last %},{% else %});{% endif %}
{% endif %}
{% endfor %}


{% endif %}
{% if data.fsrvoptions and data.fsrvoptions.changed %}
{% set addAlter = "False" %}
{% for variable in data.fsrvoptions.changed %}
{% if variable.fsrvoption and variable.fsrvoption != '' %}
{% if addAlter == "False" %}
ALTER SERVER {{ conn|qtIdent(data.name) }}
    OPTIONS ({% set addAlter = "True" %}{%endif%}
SET {{conn|qtIdent(variable.fsrvoption)}} {{variable.fsrvvalue|qtLiteral}}{% if not loop.last %},{% else %});{% endif %}
{% endif %}
{% endfor %}


{% endif %}
{# Change the privileges #}
{% if data.fsrvacl %}
{% if 'deleted' in data.fsrvacl %}
{% for priv in data.fsrvacl.deleted %}
{{ PRIVILEGE.RESETALL(conn, 'FOREIGN SERVER', priv.grantee, data.name) }}
{% endfor %}
{% endif %}
{% if 'changed' in data.fsrvacl %}
{% for priv in data.fsrvacl.changed %}
{{ PRIVILEGE.RESETALL(conn, 'FOREIGN SERVER', priv.grantee, data.name) }}
{{ PRIVILEGE.APPLY(conn, 'FOREIGN SERVER', priv.grantee, data.name, priv.without_grant, priv.with_grant) }}
{% endfor %}
{% endif %}
{% if 'added' in data.fsrvacl %}
{% for priv in data.fsrvacl.added %}
{{ PRIVILEGE.APPLY(conn, 'FOREIGN SERVER', priv.grantee, data.name, priv.without_grant, priv.with_grant) }}
{% endfor %}
{% endif %}
{% endif %}

{% endif %}
