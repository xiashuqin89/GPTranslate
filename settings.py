import os


DOMAIN = os.getenv('DOMAIN', '')
LANGUAGE = os.getenv('LANGUAGE', 'korea').split(',')
WHITE_MEMBERS = os.getenv('WHITE_MEMBERS', '').split(',')
LOGIN_URL = os.getenv('LOGIN_URL', '')

REDIS_DB_NAME = os.getenv('REDIS_DB_NAME', '127.0.0.1')
REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD', '')
REDIS_DB_PORT = int(os.getenv('REDIS_DB_PORT', '6379'))
