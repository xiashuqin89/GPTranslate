import os
import json

import pandas as pd
import numpy as np

from utils.db import RedisClient

APP_CODE = os.getenv('BKPAAS_APP_ID')
APP_ENV = os.getenv('BKPAAS_ENVIRONMENT')


class Tool:
    def __init__(self):
        self.rc = RedisClient(env="prod")

    def get_project(self, username: str, key: str = None):
        projects = self.rc.redis_client.hvals(f'{APP_CODE}:{APP_ENV}:project')
        if not projects:
            return []
        try:
            for item in projects:
                item = json.loads(item)
                if username in item['members']:
                    if key is None:
                        yield item
                    else:
                        yield item[key]
        except json.JSONDecodeError:
            return []

    def excel2text(self, data: bytes):
        pure_text = ''
        sheets = pd.read_excel(data, sheet_name=None)
        for k, v in sheets.items():
            pure_text += k
            for row in v.values.tolist():
                for col in row:
                    if col is np.nan or str(col) == 'nan':
                        pure_text += ' '
                    else:
                        pure_text += str(col)
                pure_text += '\n'
        return pure_text
