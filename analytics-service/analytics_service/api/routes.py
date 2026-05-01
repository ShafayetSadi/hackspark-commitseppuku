from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def status() -> dict:
    return {"service": "analytics-service", "status": "OK"}


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "analytics-service"}
