import os

import django
from django.conf import settings
from django.core.management import call_command

import pytest


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = True
    # If you have any test specific settings, you can declare them here,
    # e.g.
    # settings.PASSWORD_HASHERS = (
    #     'django.contrib.auth.hashers.MD5PasswordHasher',
    # )
    django.setup()
    # Note: In Django =< 1.6 you'll need to run this instead
    # settings.configure()



@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', '100_site_owner_tenant.yaml')
        call_command('loaddata', '300_archetype_tpa.yaml')
