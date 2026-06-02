from fastapi import APIRouter, HTTPException, status

from services import GenerateLoadRequest, start_generate_load, start_sync

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/generateload", status_code=status.HTTP_202_ACCEPTED)
def generate_load(payload: GenerateLoadRequest) -> dict[str, str]:
    started = start_generate_load(payload)
    if not started:
        raise HTTPException(status_code=409, detail="Load generation is already running")
    return {"message": "Load generation started. Check logs for progress."}

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def sync() -> dict[str, str]:
    start_sync()
    return {"message": "sync started. Check logs for progress."}