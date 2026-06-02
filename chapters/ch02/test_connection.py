from redis import Redis
import os

HOST = os.environ.get("REDIS_HOST", "localhost")
PORT = os.environ.get("REDIS_PORT", 6379)
USERNAME = os.environ.get("REDIS_USER")
PASSWORD = os.environ.get("REDIS_PASSWORD")

client_kwargs = {
    "host": HOST,
    "port": PORT,
    "decode_responses": True
}

if USERNAME:
    client_kwargs["username"] = USERNAME

if PASSWORD:
    client_kwargs["password"] = PASSWORD

RedisClient = Redis(**client_kwargs)


def is_reachable() -> bool:
    return RedisClient.ping()


if __name__ == "__main__":
    if is_reachable():
        print("Redis is reachable")
    else:
        print("Redis is not reachable")
