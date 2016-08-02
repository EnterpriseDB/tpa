{### SQL to fetch tablespace object properties ###}
SELECT
    ts.oid, spcname AS name, spcoptions, pg_get_userbyid(spcowner) as spcuser,
    pg_catalog.pg_tablespace_location(ts.oid) AS spclocation,
    array_to_string(spcacl::text[], ', ') as acl,
    pg_catalog.shobj_description(oid, 'pg_tablespace') AS description,
    (SELECT
        array_agg(provider || '=' || label)
    FROM pg_shseclabel sl1
    WHERE sl1.objoid=ts.oid) AS seclabels
FROM
    pg_tablespace ts
{% if tsid %}
WHERE ts.oid={{ tsid|qtLiteral }}::OID
{% endif %}
ORDER BY name
