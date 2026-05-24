from pydantic import BaseModel
from sqlmodel import Session, select

from db import Follows, Posts, Users


class UserDTO(BaseModel):
    id: int
    screen_name: str
    profile_image: str


class PostDTO(BaseModel):
    id: int
    sender_id: int
    text: str
    timestamp: int


class TimelinePostItem(BaseModel):
    user: UserDTO
    post: PostDTO


class TimelineResponse(BaseModel):
    profile_id: int
    posts: list[TimelinePostItem]


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

    timeline_posts: list[TimelinePostItem] = []
    for post, user in rows:
        if post.id is None or post.sender_id is None or user.id is None:
            # Skip incomplete rows; this keeps response DTOs strongly typed.
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
