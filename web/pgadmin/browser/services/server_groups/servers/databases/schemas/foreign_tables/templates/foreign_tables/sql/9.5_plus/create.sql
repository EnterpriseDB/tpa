{% import 'macros/schemas/security.macros' as SECLABLE %}
{% import 'macros/schemas/privilege.macros' as PRIVILEGE %}
{% set is_columns = [] %}
{% if data %}
CREATE FOREIGN TABLE {{ conn|qtIdent(data.basensp, data.name) }}(
{% if data.columns %}
{% for c in data.columns %}
{% if (not c.inheritedfrom or c.inheritedfrom =='' or  c.inheritedfrom == None or  c.inheritedfrom == 'None' ) %}
{% if is_columns.append('1') %}{% endif %}
    {{conn|qtIdent(c.attname)}} {{conn|qtTypeIdent(c.datatype) }}{% if c.typlen %}({{c.typlen}}{% if c.precision %}, {{c.precision}}{% endif %}){% endif %}{% if c.isArrayType %}[]{% endif %}{% if c.coloptions %}
{% for o in c.coloptions %}{% if o.option and o.value %}
{% if loop.first %} OPTIONS ({% endif %}{% if not loop.first %}, {% endif %}{{o.option}} {{o.value|qtLiteral}}{% if loop.last %}){% endif %}{% endif %}
{% endfor %}{% endif %}
{% if c.attnotnull %} NOT NULL{% else %} NULL{% endif %}
{% if c.typdefault %} DEFAULT {{c.typdefault}}{% endif %}
{% if c.collname %} COLLATE {{c.collname}}{% endif %}
{% if not loop.last %},
{% endif %}
{% endif %}
{% endfor %}
{% endif %}

)
{% if data.inherits %}
    INHERITS ({% for i in data.inherits %}{% if i %}{{i}}{% if not loop.last %}, {% endif %}{% endif %}{% endfor %})
{% endif %}
    SERVER {{ conn|qtIdent(data.ftsrvname) }}{% if data.ftoptions %}

{% for o in data.ftoptions %}
{% if o.option and o.value %}
{% if loop.first %}    OPTIONS ({% endif %}{% if not loop.first %}, {% endif %}{{o.option}} {{o.value|qtLiteral}}{% if loop.last %}){% endif %}{% endif %}
{% endfor %}{% endif %};
{% if data.owner %}

ALTER FOREIGN TABLE {{ conn|qtIdent(data.basensp, data.name) }}
    OWNER TO {{ data.owner }};
{% endif -%}
{% if data.constraints %}
{% for c in data.constraints %}

ALTER FOREIGN TABLE {{ conn|qtIdent(data.basensp, data.name) }}
    ADD CONSTRAINT {{ conn|qtIdent(c.conname) }} CHECK ({{ c.consrc }}){% if not c.convalidated %} NOT VALID{% endif %}{% if c.connoinherit %} NO INHERIT{% endif %};
{% endfor %}
{% endif %}
{% if data.description %}

COMMENT ON FOREIGN TABLE {{ conn|qtIdent(data.basensp, data.name) }}
    IS '{{ data.description }}';
{% endif -%}
{% if data.acl %}

{% for priv in data.acl %}
{{ PRIVILEGE.SET(conn, 'TABLE', priv.grantee, data.name, priv.without_grant, priv.with_grant, data.basensp) }}
{% endfor -%}
{% endif -%}
{% if data.seclabels %}
{% for r in data.seclabels %}
{% if r.label and r.provider %}

{{ SECLABLE.SET(conn, 'FOREIGN TABLE', data.name, r.provider, r.label, data.basensp) }}
{% endif %}
{% endfor %}
{% endif %}
{% endif %}
