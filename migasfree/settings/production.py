# -*- coding: utf-8 -*-

from .migasfree import *
from .base import *
from .functions import secret_key

# production environment
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
]

ALLOWED_HOSTS = ['*']

MIGASFREE_REPO_DIR = '/var/migasfree/repo'
MIGASFREE_KEYS_DIR = '/usr/share/migasfree-server/keys'

STATIC_ROOT = '/var/migasfree/static'
MEDIA_ROOT = MIGASFREE_REPO_DIR

SECRET_KEY = secret_key(MIGASFREE_KEYS_DIR)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'migasfree',
        'USER': 'migasfree',
        'PASSWORD': 'migasfree',
        'HOST': '',
        'PORT': '',
    }
}


def _load_settings(path):
    """
    import local settings if exists
    http://stackoverflow.com/a/1527240
    """
    if os.path.exists(path):
        # Loading configuration from path
        settings = {}
        # execfile can't modify globals directly, so we will load them manually
        execfile(path, globals(), settings)
        for setting in settings:
            globals()[setting] = settings[setting]

_load_settings("/etc/migasfree-server/settings.py")
