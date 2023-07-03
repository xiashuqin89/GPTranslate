import json
from typing import Dict

import requests

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
    headers.update({'token': DOLPH_TOKEN, 'Content-Type': 'application/json'})
    logger.error(f'headers: {headers}')
    response = requests.post(f'{DOLPH_ROOT}/{method}/',
                             headers=headers,
                             data=json.dumps(params))
    try:
        return response.json()
    except json.JSONDecodeError:
        return {}
