import logging
import os
import threading

from opentelemetry import trace
from redis import Redis
from sqlmodel import Session, select

from db import Follows, Posts
from db.session import engine
from models import Message
from utils.connection import get_connection, is_reachable

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

_lock = threading.Lock()
_is_running = False
redis: Redis


def _stream_event(message: Message) -> None:
    logger.info("Streaming post %s to user %s", message.post.id, message.user_id)
    global redis
    redis.xadd("posts", message.to_stream_payload())


def _follower_ids_for_post(post: Posts, session: Session) -> list[int]:
    statement = select(Follows.follower_id).where(Follows.followee_id == post.sender_id)
    follower_ids = session.exec(statement).all()
    return [follower_id for follower_id in follower_ids if follower_id is not None]


def _start_sync() -> None:
    offset_value = 0
    batch_size = 10

    global redis
    host = os.environ.get("MESSAGE_BROKER_HOST", "localhost")
    redis = get_connection(host=host)
    if redis is None or not is_reachable(redis):
        logger.error("Redis connection not established")
        return

    with Session(engine) as session:
        while True:
            statement = select(Posts).offset(offset_value).limit(batch_size)
            batch = session.exec(statement).all()
            # Break the loop when no records are left
            if not batch:
                break

            # Process current chunk
            for post in batch:
                for follower_id in _follower_ids_for_post(post, session):
                    _stream_event(Message(user_id=follower_id, post=post))
            offset_value += len(batch)


def start_sync() -> None:
    global _is_running
    with _lock:
        if _is_running:
            return
        _is_running = True

    def _runner():
        global _is_running
        try:
            with tracer.start_as_current_span("sync.thread") as span:
                span.set_attribute("app.batch_size", 10)
                _start_sync()
        except Exception:
            logger.exception("sync failed")
        finally:
            with _lock:
                _is_running = False

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
