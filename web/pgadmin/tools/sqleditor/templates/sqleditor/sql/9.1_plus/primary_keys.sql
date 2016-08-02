{# ============= Fetch the primary keys for given object id ============= #}
{% if obj_id %}
SELECT at.attname, ty.typname
FROM pg_attribute at LEFT JOIN pg_type ty ON (ty.oid = at.atttypid)
WHERE attrelid={{obj_id}}::oid AND attnum = ANY (
    (SELECT con.conkey FROM pg_class rel LEFT OUTER JOIN pg_constraint con ON con.conrelid=rel.oid
    AND con.contype='p' WHERE rel.relkind IN ('r','s','t') AND rel.oid = {{obj_id}}::oid)::integer[])
{% endif %}