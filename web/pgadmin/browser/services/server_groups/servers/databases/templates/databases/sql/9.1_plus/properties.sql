SELECT
    db.oid as did, db.datname as name, db.dattablespace AS spcoid,
    spcname, datallowconn, pg_encoding_to_char(encoding) AS encoding,
    pg_get_userbyid(datdba) AS datowner, datcollate, datctype, datconnlimit,
    has_database_privilege(db.oid, 'CREATE') as cancreate,
    current_setting('default_tablespace') AS default_tablespace,
    descr.description as comments,
    array_to_string(datacl::text[], ', ') AS acl
FROM pg_database db
    LEFT OUTER JOIN pg_tablespace ta ON db.dattablespace=ta.OID
    LEFT OUTER JOIN pg_shdescription descr ON (
        db.oid=descr.objoid AND descr.classoid='pg_database'::regclass
    )
WHERE {% if did %}
db.oid = {{ did|qtLiteral }}::OID{% else %}{% if name %}
db.datname = {{ name|qtLiteral }}::text{% else %}
db.oid > {{ last_system_oid|qtLiteral }}::OID
{% endif %}{% endif %}

ORDER BY datname;
