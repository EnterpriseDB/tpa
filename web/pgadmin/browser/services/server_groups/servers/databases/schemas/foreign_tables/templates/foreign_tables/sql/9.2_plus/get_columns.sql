SELECT
    attname, attndims, atttypmod, attoptions, attfdwoptions, format_type(t.oid,NULL) AS datatype,
    attnotnull, attstattarget, attnum, format_type(t.oid, att.atttypmod) AS fulltype,
    CASE WHEN length(cn.nspname) > 0 AND length(cl.collname) > 0 THEN
    concat(cn.nspname, '."', cl.collname,'"') ELSE '' END AS collname,
    (SELECT COUNT(1) from pg_type t2 WHERE t2.typname=t.typname) > 1 AS isdup,
    pg_catalog.pg_get_expr(def.adbin, def.adrelid) AS typdefault,
    (
        attname || ' ' || format_type(t.oid, att.atttypmod) || ' ' ||
        (
            CASE WHEN array_length(attfdwoptions, 1)>0
            THEN concat('OPTIONS (', array_to_string(attfdwoptions, ', '), ')') ELSE ''
            END
        ) || ' ' ||
        (
            CASE WHEN attnotnull='true'
            THEN 'NOT NULL' ELSE 'NULL'
            END
        ) || ' ' ||
        (
            CASE WHEN pg_catalog.pg_get_expr(def.adbin, def.adrelid)<>''
            THEN 'DEFAULT ' || pg_catalog.pg_get_expr(def.adbin, def.adrelid)
            ELSE '' END
        )
    ) as strcolumn
FROM
    pg_attribute att
JOIN
    pg_type t ON t.oid=atttypid
JOIN
    pg_namespace nsp ON t.typnamespace=nsp.oid
LEFT OUTER JOIN
    pg_attrdef def ON adrelid=att.attrelid AND adnum=att.attnum
LEFT OUTER JOIN
    pg_type b ON t.typelem=b.oid
LEFT OUTER JOIN
    pg_collation cl ON t.typcollation=cl.oid
LEFT OUTER JOIN
    pg_namespace cn ON cl.collnamespace=cn.oid
WHERE
    att.attrelid={{foid}}::oid
    AND attnum>0
ORDER by attnum;
