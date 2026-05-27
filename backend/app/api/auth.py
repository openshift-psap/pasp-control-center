from fastapi import APIRouter, Depends

from app.core.auth import require_auth

router = APIRouter()


@router.get("/check")
async def check_auth(user: str = Depends(require_auth)):
    return {"authenticated": True, "username": user}
