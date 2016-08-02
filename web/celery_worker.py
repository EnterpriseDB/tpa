import os
from pgadmin import celery, create_app

app = create_app()
app.app_context().push()