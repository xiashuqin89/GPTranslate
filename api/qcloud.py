import json
from typing import Dict

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models

from log import logger
from settings import (
    QCLOUD_SECRET_ID as SECRET_ID, QCLOUD_SECRET_KEY as SECRET_KEY
)


class QCloud:
    def __init__(self, product: str, region: str):
        self.region = region
        http_profile = HttpProfile()
        http_profile.endpoint = f"{product}.tencentcloudapi.com"
        self.cred = credential.Credential(SECRET_ID, SECRET_KEY)
        self.client_profile = ClientProfile()
        self.client_profile.httpProfile = http_profile

    def post_handle(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except TencentCloudSDKException as e:
                logger.error(f'{func.__name__} error: {args} {kwargs} {e}')
                return {}
        return wrapper

    @post_handle
    def handle_request(self, service: str, client, **kwargs):
        req = getattr(models, f'{service}Request')()
        req.from_json_string(json.dumps(kwargs))
        resp = getattr(client, service)(req)
        try:
            return json.loads(resp.to_json_string())
        except json.JSONDecodeError:
            return {}


class Tmt(QCloud):
    PRODUCT = 'tmt'

    def __init__(self, region: str = 'ap-beijing'):
        super(Tmt, self).__init__(self.PRODUCT, region)
        self.client = tmt_client.TmtClient(self.cred, region, self.client_profile)

    def translate(self, **kwargs) -> Dict:
        """
        "SourceText": "你好",
        "Source": "zh",
        "Target": "en",
        "ProjectId": 0
        """
        return self.handle_request('TextTranslate', self.client,  **kwargs)
