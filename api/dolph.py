import json
from typing import Dict

import requests

from settings import DOLPH_ROOT, DOLPH_TOKEN
from log import logger


def translate(headers: Dict, method='translate', **params):
    """
    text
    translate_type: qcloud/chatgpt
    """
    headers.update({'token': DOLPH_TOKEN, 'Content-Type': 'application/json'})
    logger.info(f'headers: {headers}')
    logger.info(f'method: {method}')
    logger.info(f'params: {params}')
    response = requests.post(f'{DOLPH_ROOT}/{method}/',
                             headers=headers,
                             data=json.dumps(params))
    try:
        return response.json()
    except json.JSONDecodeError:
        return {}
