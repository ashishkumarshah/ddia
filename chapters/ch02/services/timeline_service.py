import os

from pydantic import BaseModel
from sqlmodel import Session, col, select

from db import Follows, Posts, Users
from dtos import PostDTO, UserDTO
from utils.connection import get_connection, is_reachable


class TimelinePostItem(BaseModel):
    user: UserDTO
    post: PostDTO


class TimelineResponse(BaseModel):
    profile_id: int
    posts: list[TimelinePostItem]


def _build_timeline_response(profile_id: int, rows: list[tuple[Posts, Users]]) -> TimelineResponse:
    timeline_posts: list[TimelinePostItem] = []
    for post, user in rows:
        if post.id is None or post.sender_id is None or user.id is None:
            continue

        timeline_posts.append(
            TimelinePostItem(
                user=UserDTO(
                    id=user.id,
                    screen_name=user.screen_name,
                    profile_image=user.profile_image,
                ),
                post=PostDTO(
                    id=post.id,
                    sender_id=post.sender_id,
                    text=post.text,
                    timestamp=post.timestamp,
                ),
            )
        )

    return TimelineResponse(profile_id=profile_id, posts=timeline_posts)


def get_timeline(profile_id: int, limit: int = 1000, session: Session | None = None) -> TimelineResponse:
    # profile_id is the "current_user" from the SQL you shared.
    if session is None:
        # Keep call-sites working until DB session wiring is added in the route layer.
        return TimelineResponse(profile_id=profile_id, posts=[])

    statement = (
        select(Posts, Users)
        .join(Follows, Posts.sender_id == Follows.followee_id)
        .join(Users, Posts.sender_id == Users.id)
        .where(Follows.follower_id == profile_id)
        .order_by(Posts.timestamp.desc())
        .limit(limit)
    )

    rows = session.exec(statement).all()
    return _build_timeline_response(profile_id=profile_id, rows=rows)


def get_timeline_v2(profile_id: int, limit: int = 1000, session: Session | None = None) -> TimelineResponse:
    if session is None:
        return TimelineResponse(profile_id=profile_id, posts=[])

    host = os.environ.get("MESSAGE_BOX_HOST", "localhost")
    redis = get_connection(host=host)
    if redis is None or not is_reachable(redis):
        return TimelineResponse(profile_id=profile_id, posts=[])

    post_ids = redis.smembers(f"message:{profile_id}")
    if not post_ids:
        return TimelineResponse(profile_id=profile_id, posts=[])

    ids = [int(post_id) for post_id in post_ids]
    statement = (
        select(Posts, Users)
        .join(Users, Posts.sender_id == Users.id)
        .where(col(Posts.id).in_(ids))
    )
    rows = session.exec(statement).all()
    sorted_rows = sorted(rows, key=lambda row: row[0].timestamp, reverse=True)[:limit]
    return _build_timeline_response(profile_id=profile_id, rows=sorted_rows)
