import os


DOMAIN = os.getenv('DOMAIN', '')
WHITE_MEMBERS = os.getenv('WHITE_MEMBERS', '').split(',')
LOGIN_URL = os.getenv('LOGIN_URL', '')

REDIS_DB_NAME = os.getenv('REDIS_DB_NAME')
REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD')
REDIS_DB_PORT = os.getenv('REDIS_DB_PORT')
