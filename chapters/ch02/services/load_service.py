import logging
import random
import threading
import time
from collections.abc import Sequence

from opentelemetry import trace
from pydantic import BaseModel, Field, model_validator
from sqlmodel import Session

from db import Follows, Posts, Users
from db.session import engine

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class PercentBand(BaseModel):
    user_percent: float = Field(gt=0)
    value_percent: float = Field(gt=0)


class GenerateLoadRequest(BaseModel):
    num_users: int = Field(gt=0)
    num_posts: int = Field(ge=0)
    num_follows: int = Field(ge=0)
    seed: int = 42
    post_activity_bands: list[PercentBand]
    follow_bands: list[PercentBand]

    @model_validator(mode="after")
    def validate_bands(self):
        def _sum(values: Sequence[PercentBand], attr: str) -> float:
            return sum(getattr(v, attr) for v in values)

        if round(_sum(self.post_activity_bands, "user_percent"), 6) != 100.0:
            raise ValueError("post_activity_bands user_percent must sum to 100")
        if round(_sum(self.post_activity_bands, "value_percent"), 6) != 100.0:
            raise ValueError("post_activity_bands value_percent must sum to 100")
        if round(_sum(self.follow_bands, "user_percent"), 6) != 100.0:
            raise ValueError("follow_bands user_percent must sum to 100")
        if round(_sum(self.follow_bands, "value_percent"), 6) != 100.0:
            raise ValueError("follow_bands value_percent must sum to 100")
        return self


_lock = threading.Lock()
_is_running = False


def _bucketize_users(user_ids: list[int], bands: list[PercentBand], rng: random.Random) -> list[list[int]]:
    ids = user_ids[:]
    rng.shuffle(ids)

    buckets: list[list[int]] = []
    start = 0
    for i, band in enumerate(bands):
        if i == len(bands) - 1:
            end = len(ids)
        else:
            size = int(len(ids) * (band.user_percent / 100.0))
            end = min(len(ids), start + size)
        buckets.append(ids[start:end])
        start = end
    return buckets


def _counts_from_percent(total: int, percents: list[float]) -> list[int]:
    raw = [total * (p / 100.0) for p in percents]
    base = [int(x) for x in raw]
    remainder = total - sum(base)
    frac_order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in frac_order[:remainder]:
        base[i] += 1
    return base


def _generate_load(payload: GenerateLoadRequest) -> None:
    rng = random.Random(payload.seed)
    user_ids = list(range(1, payload.num_users + 1))

    logger.info("generateload started: users=%s posts=%s follows=%s", payload.num_users, payload.num_posts, payload.num_follows)

    with Session(engine) as session:
        users = [Users(id=i, screen_name=f"firstname{i} lastname{i}", profile_image=f"pic-{i}.jpg") for i in user_ids]
        session.add_all(users)
        session.commit()
        logger.info("users inserted: %s", len(users))

        post_buckets = _bucketize_users(user_ids, payload.post_activity_bands, rng)
        post_counts = _counts_from_percent(payload.num_posts, [b.value_percent for b in payload.post_activity_bands])

        ts = int(time.time())
        posts: list[Posts] = []
        for bucket, bucket_posts in zip(post_buckets, post_counts):
            if not bucket or bucket_posts <= 0:
                continue
            base = bucket_posts // len(bucket)
            rem = bucket_posts % len(bucket)
            for idx, uid in enumerate(bucket):
                count = base + (1 if idx < rem else 0)
                for _ in range(count):
                    ts += 1
                    posts.append(Posts(sender_id=uid, text=f"benchmark-post user={uid} ts={ts}", timestamp=ts))
        if posts:
            session.add_all(posts)
            session.commit()
        logger.info("posts inserted: %s", len(posts))

        follow_buckets = _bucketize_users(user_ids, payload.follow_bands, rng)
        follow_counts = _counts_from_percent(payload.num_follows, [b.value_percent for b in payload.follow_bands])
        follows_set: set[tuple[int, int]] = set()

        for bucket, edge_count in zip(follow_buckets, follow_counts):
            if not bucket or edge_count <= 0:
                continue
            attempts = 0
            while edge_count > 0 and attempts < max(1000, edge_count * 10):
                followee = rng.choice(bucket)
                follower = rng.choice(user_ids)
                attempts += 1
                if follower == followee:
                    continue
                pair = (follower, followee)
                if pair in follows_set:
                    continue
                follows_set.add(pair)
                edge_count -= 1

        follows = [Follows(follower_id=fid, followee_id=tid) for fid, tid in follows_set]
        if follows:
            session.add_all(follows)
            session.commit()
        logger.info("follows inserted: %s", len(follows))

    logger.info("generateload completed")


def start_generate_load(payload: GenerateLoadRequest) -> bool:
    global _is_running
    with _lock:
        if _is_running:
            return False
        _is_running = True

    def _runner():
        global _is_running
        try:
            with tracer.start_as_current_span("generateload.thread") as span:
                span.set_attribute("app.num_users", payload.num_users)
                span.set_attribute("app.num_posts", payload.num_posts)
                span.set_attribute("app.num_follows", payload.num_follows)
                span.set_attribute("app.seed", payload.seed)
                _generate_load(payload)
        except Exception:
            logger.exception("generateload failed")
        finally:
            with _lock:
                _is_running = False

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return True
