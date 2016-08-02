{# ===== Fetch list of Database object types(Functions) ====== #}
{% if type and node_id and nspname %}
{% set func_type = 'Trigger Function' if type == 'trigger_function' else 'Procedure' if type == 'procedure' else 'Function' %}
{% set icon = 'icon-function' if type == 'function' else 'icon-procedure' if type == 'procedure' else 'icon-trigger_function' %}
SELECT
    pr.oid,
    pg_get_function_identity_arguments(pr.oid) AS proargs,
    pr.proname AS name,
    '{{ func_type }}' AS object_type,
    '{{ nspname }}' AS nspname,
    '{{ icon }}' AS icon
FROM
    pg_proc pr
JOIN pg_type typ ON typ.oid=prorettype
JOIN pg_namespace typns ON typns.oid=typ.typnamespace
JOIN pg_language lng ON lng.oid=prolang
LEFT OUTER JOIN pg_description des ON (des.objoid=pr.oid AND des.classoid='pg_proc'::regclass)
WHERE
    proisagg = FALSE AND pronamespace = {{ node_id }}::oid
    AND typname {{ 'NOT' if type != 'trigger_function' else '' }} IN ('trigger', 'event_trigger')
    AND pr.protype = {{ 0 if type != 'procedure' else 1 }}
ORDER BY
    proname
{% endif %}
