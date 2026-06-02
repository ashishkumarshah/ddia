import logging
import os

from models import Message
from utils.connection import get_connection, is_reachable

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def _to_message(payload: dict[str, str]) -> Message:
    return Message.from_stream_payload(payload)


def process_event(message: Message, messagebox) -> None:
    if message.post.id is None:
        logger.warning("Skipping message for user %s with missing post id", message.user_id)
        return

    messagebox.sadd(f"message:{message.user_id}", message.post.id)
    logger.info("Added post %s to messagebox set for user %s", message.post.id, message.user_id)


def read_posts_stream() -> None:
    broker_host = os.environ.get("MESSAGE_BROKER_HOST", "localhost")
    messagebox_host = os.environ.get("MESSAGE_BOX_HOST", "localhost")
    redis = get_connection(host=broker_host)
    messagebox = get_connection(host=messagebox_host)
    if redis is None or not is_reachable(redis):
        logger.error("Redis connection not established")
        return
    if messagebox is None or not is_reachable(messagebox):
        logger.error("Messagebox connection not established")
        return

    last_id = "0-0"

    while True:
        stream_response = redis.xread({"posts": last_id}, count=BATCH_SIZE)
        if not stream_response:
            break

        for _, entries in stream_response:
            for entry_id, payload in entries:
                process_event(_to_message(payload), messagebox)
                last_id = entry_id


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    read_posts_stream()
