import os


DOMAIN = os.getenv('DOMAIN', '')
WHITE_MEMBERS = os.getenv('WHITE_MEMBERS', '').split(',')
LOGIN_URL = os.getenv('LOGIN_URL', '')
