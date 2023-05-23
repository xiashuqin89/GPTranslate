import os
import json

import redis

from log import logger
from settings import REDIS_DB_NAME, REDIS_DB_PASSWORD, REDIS_DB_PORT


class RedisClient:
    """
    redis操作
    """

    def __init__(self, db_name="0", env="dev"):
        self.db_name = db_name

        if env == "dev":
            self.host = "localhost"
            self.password = ""
            self.port = 6379
            self.redis_client = redis.Redis(
                host=self.host, port=self.port, db=self.db_name, decode_responses=True
            )
        else:
            self.host = REDIS_DB_NAME
            self.password = REDIS_DB_PASSWORD
            self.port = REDIS_DB_PORT
            self.redis_client = redis.Redis(
                host=self.host,
                password=self.password,
                port=self.port,
                db=self.db_name,
                decode_responses=True,
            )

    def set(self, key, data, ex=None, nx=False):
        self.redis_client.set(key, data, ex=ex, nx=nx)

    def get(self, key):
        data = self.redis_client.get(key)
        try:
            data = json.loads(data)
        except Exception as e:
            data = []
            logger.error("REDIS GET ERR [{}]".format(str(e)))

        return data

    def hash_set(self, name, key, val):
        self.redis_client.hset(name, key, val)

    def hash_get(self, name, key):
        return self.redis_client.hget(name, key)

    def pipe_set(self, data):
        with self.redis_client.pipeline(transaction=False) as pipe:
            for k, v in data.items():
                pipe.set(k, json.dumps(v))
            pipe.execute()
