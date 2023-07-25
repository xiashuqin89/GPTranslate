import json
from typing import Dict

import requests
from requests_oauth2 import OAuth2BearerToken

from settings import DOLPH_ROOT, DOLPH_TOKEN
from log import logger


def translate(headers: Dict, method='translate', **params):
    """
    text
    translate_type: qcloud/chatgpt
    file
    file_name
    extract_type
    """
    with requests.Session() as client:
        client.auth = OAuth2BearerToken(DOLPH_TOKEN)
        # client.headers = {'Content-Type': 'application/json'}
        client.headers.update(headers)
        logger.info(f'headers: {headers}')
        response = client.post(f'{DOLPH_ROOT}/{method}/',
                               headers=headers,
                               data=json.dumps(params))
        try:
            return response.json()
        except json.JSONDecodeError:
            return {}
