SELECT 'fsrvacl' as deftype, COALESCE(gt.rolname, 'PUBLIC') grantee, g.rolname grantor, array_agg(privilege_type) as privileges, array_agg(is_grantable) as grantable
FROM
    (SELECT
        d.grantee, d.grantor, d.is_grantable,
        CASE d.privilege_type
        WHEN 'USAGE' THEN 'U'
        ELSE 'UNKNOWN'
        END AS privilege_type
    FROM
        (SELECT srvacl FROM pg_foreign_server fsrv
            LEFT OUTER JOIN pg_shdescription descr ON (
            fsrv.oid=descr.objoid AND descr.classoid='pg_foreign_server'::regclass)
{% if fsid %}
        WHERE fsrv.oid = {{ fsid|qtLiteral }}::OID
{% endif %}
        ) acl,
        (SELECT (d).grantee AS grantee, (d).grantor AS grantor, (d).is_grantable AS is_grantable,
                (d).privilege_type AS privilege_type
        FROM (SELECT aclexplode(srvacl) as d FROM pg_foreign_server fsrv1
        {% if fsid %}
                WHERE fsrv1.oid = {{ fsid|qtLiteral }}::OID ) a
        {% endif %}
        ) d
    ) d
    LEFT JOIN pg_catalog.pg_roles g ON (d.grantor = g.oid)
    LEFT JOIN pg_catalog.pg_roles gt ON (d.grantee = gt.oid)
GROUP BY g.rolname, gt.rolname
