import json
from typing import Dict

import requests

from settings import DOLPH_ROOT, DOLPH_TOKEN


def translate(headers: Dict, method='translate', **params):
    """
    text
    translate_type: qcloud/chatgpt
    """
    headers.update({'token': DOLPH_TOKEN, 'Content-Type': 'application/json'})
    response = requests.post(f'{DOLPH_ROOT}/{method}/',
                             headers=headers,
                             data=json.dumps(params))
    try:
        return response.json()
    except json.JSONDecodeError:
        return {}
