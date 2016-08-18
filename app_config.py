#!/usr/bin/env python

"""
Project-wide application configuration.
"""

import os

from authomatic.providers import oauth2
from authomatic import Authomatic

"""
NAMES
"""
# The name and favicon of your company for titlebars
COMPANY_NAME = 'APM Reports'
FAVICON_URL = ''

# Project name in urls
# Use dashes, not underscores!
PROJECT_SLUG = 'dailygraphics'

# Slug for assets dir on S3
ASSETS_SLUG = PROJECT_SLUG

# The name of the repository containing the source
REPOSITORY_NAME = 'dailygraphics'
REPOSITORY_URL = 'git@github.com:wcraft/%s.git' % REPOSITORY_NAME
REPOSITORY_ALT_URL = None # 'git@bitbucket.org:nprapps/%s.git' % REPOSITORY_NAME'

# The name and path to the folder containing the graphics
GRAPHICS_NAME = 'graphics'
GRAPHICS_PATH = '/Users/wcraft/Code/dailygraphics/graphics' #os.path.abspath('../%s' % GRAPHICS_NAME)

# Path to the graphic templates
TEMPLATES_PATH = os.path.abspath('graphic_templates')

"""
OAUTH
"""

GOOGLE_OAUTH_CREDENTIALS_PATH = '~/.google_oauth_credentials'

authomatic_config = {
    'google': {
        'id': 1,
        'class_': oauth2.Google,
        'consumer_key': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
        'consumer_secret': os.environ.get('GOOGLE_OAUTH_CONSUMER_SECRET'),
        'scope': ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/userinfo.email'],
        'offline': True,
    },
}

authomatic = Authomatic(authomatic_config, os.environ.get('AUTHOMATIC_SALT'))

"""
DEPLOYMENT
"""
PRODUCTION_S3_BUCKET = {
    'bucket_name': '', # 'apps.npr.org'
    'region': '' # 'us.east-1'
}

STAGING_S3_BUCKET = {
    'bucket_name': '', # 'stage-apps.npr.org'
    'region': '' # 'us.east-1'
}

ASSETS_S3_BUCKET = {
    'bucket_name': '',  # 'assets.apps.npr.org'
    'region': '' # 'us.east-1'
}

S3_HOST = ''

def get_bucket_url(bucket):
    return 'http://%s.s3-website-%s.amazonaws.com/%s' % (
        bucket['bucket_name'],
        bucket['region'],
        PROJECT_SLUG
        )

#PRODUCTION_S3_URL = get_bucket_url(PRODUCTION_S3_BUCKET) + '/%s' % GRAPHICS_NAME
#STAGING_S3_URL = get_bucket_url(STAGING_S3_BUCKET) + '/%s' % GRAPHICS_NAME
#ASSETS_S3_URL = get_bucket_url(ASSETS_S3_BUCKET)

DEFAULT_MAX_AGE = 20
ASSETS_MAX_AGE = 300


"""
ANALYTICS
"""

GOOGLE_ANALYTICS = {
    'ACCOUNT_ID': '' # 'UA-XXXXXXX-XX'
}

# These variables will be set at runtime. See configure_targets() below
S3_BUCKET = None
S3_BASE_URL = ''
S3_DEPLOY_URL = None
DEBUG = True

def configure_targets(deployment_target):
    """
    Configure deployment targets. Abstracted so this can be
    overriden for rendering before deployment.
    """
    global S3_BUCKET
    global S3_BASE_URL
    global S3_DEPLOY_URL
    global DEBUG
    global DEPLOYMENT_TARGET

    if deployment_target == 'production':
        S3_BUCKET = PRODUCTION_S3_BUCKET
        S3_BASE_URL = PRODUCTION_S3_URL
        S3_DEPLOY_URL = 's3://%s/%s' % (S3_BUCKET['bucket_name'], PROJECT_SLUG)
        DEBUG = False
    elif deployment_target == 'staging':
        S3_BUCKET = STAGING_S3_BUCKET
        S3_BASE_URL = STAGING_S3_URL
        S3_DEPLOY_URL = 's3://%s/%s' % (S3_BUCKET['bucket_name'], PROJECT_SLUG)
        DEBUG = True
    else:
        S3_BUCKET = None
        S3_BASE_URL = 'http://127.0.0.1:8000'
        S3_DEPLOY_URL = None
        DEBUG = True

    DEPLOYMENT_TARGET = deployment_target

"""
Run automated configuration
"""
DEPLOYMENT_TARGET = os.environ.get('DEPLOYMENT_TARGET', None)

configure_targets(DEPLOYMENT_TARGET)
