import time

from sqlmodel import Session, col, select

from db import Posts
from dtos import PostDTO


def create_tweet(sender_id: int, text: str, session: Session) -> None:
    post = Posts(sender_id=sender_id, text=text, timestamp=int(time.time()))
    session.add(post)
    session.commit()



def get_tweet(tweet_id: int, session: Session) -> PostDTO | None:
    post = session.get(Posts, tweet_id)
    if post is None or post.id is None or post.sender_id is None:
        return None
    post_id = post.id
    sender_id = post.sender_id
    return PostDTO(id=post_id, sender_id=sender_id, text=post.text, timestamp=post.timestamp)


def get_tweets_by_ids(ids: list[int], session: Session) -> list[PostDTO]:
    if not ids:
        return []

    statement = select(Posts).where(col(Posts.id).in_(ids)).order_by(Posts.timestamp.desc())
    posts = session.exec(statement).all()

    results: list[PostDTO] = []
    for post in posts:
        if post.id is None or post.sender_id is None:
            continue
        post_id = post.id
        sender_id = post.sender_id
        results.append(PostDTO(id=post_id, sender_id=sender_id, text=post.text, timestamp=post.timestamp))
    return results
