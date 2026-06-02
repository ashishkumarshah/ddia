import json
from dataclasses import dataclass

from db import Posts


@dataclass
class Message:
    user_id: int
    post: Posts

    def to_stream_payload(self) -> dict[str, str | int]:
        return {
            "user_id": self.user_id,
            "post": self.post.model_dump_json(),
        }

    @classmethod
    def from_stream_payload(cls, payload: dict[str, str]) -> "Message":
        post_data = json.loads(payload["post"])
        post = Posts(
            id=int(post_data["id"]) if post_data.get("id") is not None else None,
            sender_id=int(post_data["sender_id"]) if post_data.get("sender_id") is not None else None,
            text=post_data["text"],
            timestamp=int(post_data["timestamp"]),
        )
        return cls(user_id=int(payload["user_id"]), post=post)
