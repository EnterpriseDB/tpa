ALTER TABLE {{ conn|qtIdent(data.schema, data.table) }}
    VALIDATE CONSTRAINT {{ conn|qtIdent(data.name) }};