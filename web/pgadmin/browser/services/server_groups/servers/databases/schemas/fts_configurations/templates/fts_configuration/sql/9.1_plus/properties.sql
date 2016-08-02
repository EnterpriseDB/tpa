{# FETCH properties for FTS CONFIGURATION #}
SELECT
    cfg.oid,
    cfg.cfgname as name,
    pg_get_userbyid(cfg.cfgowner) as owner,
    cfg.cfgparser as parser,
    cfg.cfgnamespace as schema,
    parser.prsname as prsname,
    description
FROM
    pg_ts_config cfg
    LEFT OUTER JOIN pg_ts_parser parser
    ON parser.oid=cfg.cfgparser
    LEFT OUTER JOIN pg_description des
    ON (des.objoid=cfg.oid AND des.classoid='pg_ts_config'::regclass)
WHERE
{% if scid %}
    cfg.cfgnamespace = {{scid}}::OID
{% elif name %}
    cfg.cfgname = {{name|qtLiteral}}
{% endif %}
{% if cfgid %}
    AND cfg.oid = {{cfgid}}::OID
{% endif %}
ORDER BY cfg.cfgname
