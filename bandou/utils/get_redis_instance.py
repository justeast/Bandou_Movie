import redis
from django.conf import settings


def get_redis_instance():
    """从redis连接池中获取redis实例"""
    pool = redis.ConnectionPool(**settings.REDIS_CONFIG)
    return redis.Redis(connection_pool=pool)
