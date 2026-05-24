from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace
from sqlmodel import Session

from db import get_session
from services import (
    GenerateLoadRequest,
    TimelineResponse,
    get_timeline as get_timeline_service,
    start_generate_load,
)

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/{profile_id}")
def get_timeline(
    profile_id: int,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> TimelineResponse:
    span = trace.get_current_span()
    span.set_attribute("app.profile_id", profile_id)
    span.set_attribute("app.timeline_limit", limit)
    return get_timeline_service(profile_id=profile_id, limit=limit, session=session)


@router.post("/generateload", status_code=status.HTTP_202_ACCEPTED)
def generate_load(payload: GenerateLoadRequest) -> dict[str, str]:
    started = start_generate_load(payload)
    if not started:
        raise HTTPException(status_code=409, detail="Load generation is already running")
    return {"message": "Load generation started. Check logs for progress."}
