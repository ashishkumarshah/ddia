from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from db import get_session
from dtos import PostDTO
from services.tweet_service import create_tweet, get_tweet, get_tweets_by_ids


class CreateTweetRequest(BaseModel):
    text: str


router = APIRouter(prefix="/tweet", tags=["tweet"])


@router.post("/{sender_id}", status_code=status.HTTP_201_CREATED)
def post_tweet(sender_id: int, payload: CreateTweetRequest, session: Session = Depends(get_session)) -> dict[str, str]:
    create_tweet(sender_id=sender_id, text=payload.text, session=session)
    return {"message": "Tweet created"}


@router.get("/{id}")
def fetch_tweet(id: int, session: Session = Depends(get_session)) -> PostDTO:
    tweet = get_tweet(tweet_id=id, session=session)
    if tweet is None:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return tweet


@router.post("")
def fetch_tweets(ids: list[int], session: Session = Depends(get_session)) -> list[PostDTO]:
    return get_tweets_by_ids(ids=ids, session=session)
