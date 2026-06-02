from fastapi import APIRouter, Depends
from opentelemetry import trace
from sqlmodel import Session

from db import get_session
from services import TimelineResponse, get_timeline_v2 as get_timeline_service

router = APIRouter(prefix="/v2/timeline", tags=["timeline"])


@router.get("/{profile_id}")
def get_timeline(
    profile_id: int,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> TimelineResponse:
    span = trace.get_current_span()
    span.set_attribute("app.profile_id", profile_id)
    span.set_attribute("app.timeline_limit", limit)
    span.set_attribute("app.timeline_version", "v2")
    return get_timeline_service(profile_id=profile_id, limit=limit, session=session)
