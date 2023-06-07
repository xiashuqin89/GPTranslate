from typing import Any, Optional, Dict

import requests
from requests.auth import HTTPBasicAuth

from settings import (
    BK_REPO_USERNAME, BK_REPO_PASSWORD, BK_REPO_ROOT
)
from log import logger
from exceptions import ActionFailed


class BKRepo:
    def __init__(self):
        self.api_root = BK_REPO_ROOT
        self.basic = HTTPBasicAuth(BK_REPO_USERNAME, BK_REPO_PASSWORD)

    def _handle_api_result(self, result: Optional[Dict[str, Any]]) -> Any:
        if isinstance(result, dict):
            if result.get('result', False) or result.get('code', 0) == 0:
                return result.get('data')
            logger.error(result)
            raise ActionFailed

    def call_action(self, action: str, method: str, **params) -> Any:
        params.update({'auth': self.basic})

        url = f"{self.api_root}/{action}"
        response = getattr(requests, method)(url, **params)
        try:
            return self._handle_api_result(response.json())
        except TypeError:
            return {}

    def upload(self, project: str, repo: str, abs_path: str, **params):
        """
        files/data
        """
        return self.call_action(f'generic/{project}/{repo}/{abs_path}', 'put', **params)

    def download(self, project: str, repo: str, abs_path: str):
        return self.call_action(f'generic/{project}/{repo}/{abs_path}?download=true', 'get')

    def search(self, rule: Dict):
        """
        {
            "page":{
                "pageNumber":1,
                "pageSize":1000
            },
            "sort":{
                "properties":["folder","lastModifiedDate"],
                "direction":"DESC"
            },
            "rule":{
                "rules":[
                    {
                        "field":"projectId",
                        "value":"opsbot2",
                        "operation":"EQ"
                    },
                    {
                        "field":"repoName",
                        "value":"translate",
                        "operation":"EQ"
                    },
                    {
                        "field":"path",
                        "value":"/target/",
                        "operation":"EQ"
                    }
                ],
                "relation":"AND"
            }
        }
        """
        return self.call_action('repository/api/node/search',
                                'post',
                                json={
                                    "page": {"pageNumber": 1, "pageSize": 1000},
                                    "sort": {"properties": ["folder", "lastModifiedDate"],
                                             "direction": "DESC"},
                                    "rule": rule
                                })
