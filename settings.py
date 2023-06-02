import os


DOMAIN = os.getenv('DOMAIN', '')
WHITE_MEMBERS = os.getenv('WHITE_MEMBERS', '').split(',')
LOGIN_URL = os.getenv('LOGIN_URL', '')
LANGUAGE = os.getenv('LANGUAGE', 'ko,en').split(',')
MODEL = os.getenv('MODEL', 'chatgpt,qcloud').split(',')

REDIS_DB_NAME = os.getenv('REDIS_DB_NAME', '127.0.0.1')
REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD', '')
REDIS_DB_PORT = int(os.getenv('REDIS_DB_PORT', '6379'))

QCLOUD_SECRET_ID = os.getenv('QCLOUD_SECRET_ID', '')
QCLOUD_SECRET_KEY = os.getenv('QCLOUD_SECRET_KEY', '')

BK_REPO_ROOT = os.getenv('BK_REPO_ROOT')
BK_REPO_USERNAME = os.getenv('BK_REPO_USERNAME')
BK_REPO_PASSWORD = os.getenv('BK_REPO_PASSWORD')

DOLPH_ROOT = os.getenv('DOLPH_ROOT')
DOLPH_TOKEN = os.getenv('DOLPH_TOKEN')
