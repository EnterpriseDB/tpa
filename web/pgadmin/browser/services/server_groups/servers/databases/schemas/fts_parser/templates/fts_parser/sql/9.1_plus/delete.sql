{# FETCH FTS PARSER NAME Statement #}
{% if pid %}
SELECT
    p.prsname AS name,
    (
        SELECT
            nspname
        FROM
            pg_namespace
        WHERE
            oid = p.prsnamespace
    ) as schema
FROM
    pg_ts_parser p LEFT JOIN pg_description d
    ON d.objoid=p.oid AND d.classoid='pg_ts_parser'::regclass
WHERE
    p.oid = {{pid}}::OID;
{% endif %}

{# DROP FTS PARSER Statement #}
{% if schema and name %}
DROP TEXT SEARCH PARSER {{conn|qtIdent(schema)}}.{{conn|qtIdent(name)}} {% if cascade %}CASCADE{%endif%};
{% endif %}