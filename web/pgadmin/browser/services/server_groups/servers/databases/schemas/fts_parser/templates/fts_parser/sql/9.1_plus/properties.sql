{# FETCH properties for FTS PARSER #}
SELECT
    prs.oid,
    prs.prsname as name,
    prs.prsstart,
    prs.prstoken,
    prs.prsend,
    prs.prslextype,
    prs.prsheadline,
    description,
    prs.prsnamespace AS schema
FROM
    pg_ts_parser prs
    LEFT OUTER JOIN pg_description des
ON
    (
    des.objoid=prs.oid
    AND des.classoid='pg_ts_parser'::regclass
    )
WHERE
{% if scid %}
    prs.prsnamespace = {{scid}}::OID
{% elif name %}
    prs.prsname = {{name|qtLiteral}}
{% endif %}
{% if pid %}
    AND prs.oid = {{pid}}::OID
{% endif %}
ORDER BY
    prs.prsname