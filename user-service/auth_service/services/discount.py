from fastapi import HTTPException

from shared.app_core.central_api import CentralAPIClient


def compute_discount(score: int) -> int:
    if 80 <= score <= 100:
        return 20
    if 60 <= score <= 79:
        return 15
    if 40 <= score <= 59:
        return 10
    if 20 <= score <= 39:
        return 5
    return 0


async def get_user_discount(client: CentralAPIClient, *, user_id: int) -> dict:
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user id")

    payload = await client.get(f"/api/data/users/{user_id}")
    security_score = int(payload["securityScore"])
    return {
        "userId": user_id,
        "securityScore": security_score,
        "discountPercent": compute_discount(security_score),
    }
