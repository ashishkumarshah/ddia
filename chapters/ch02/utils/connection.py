'''
Redis connection utilities
'''

from redis import Redis


def get_connection(name: str = None, host: str = "localhost", port: int = 6379):
    client_kwargs = {
        "host": host,
        "port": port,
        "decode_responses": True
    }

    redis = Redis(**client_kwargs)

    if name is not None:
        redis.client_setname(name)

    return redis


def is_reachable(redis: Redis) -> bool:
    if redis is None:
        return False
    return redis.ping()
