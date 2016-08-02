{# Update the row with primary keys (specified in primary_keys) #}
UPDATE {{ conn|qtIdent(nsp_name, object_name) }} SET
{% for col in data_to_be_saved %}
{% if not loop.first %}, {% endif %}{{ conn|qtIdent(col) }} = {{ data_to_be_saved[col]|qtLiteral }}{% endfor %}
 WHERE
{% for pk in primary_keys %}
{% if not loop.first %} AND {% endif %}{{ conn|qtIdent(pk) }} = {{ primary_keys[pk]|qtLiteral }}{% endfor %};