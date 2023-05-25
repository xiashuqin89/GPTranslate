import os


DOMAIN = os.getenv('DOMAIN', '')
WHITE_MEMBERS = os.getenv('WHITE_MEMBERS', '').split(',')
LOGIN_URL = os.getenv('LOGIN_URL', '')
LANGUAGE = os.getenv('LANGUAGE', 'ko,en').split(',')

REDIS_DB_NAME = os.getenv('REDIS_DB_NAME', '127.0.0.1')
REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD', '')
REDIS_DB_PORT = int(os.getenv('REDIS_DB_PORT', '6379'))
