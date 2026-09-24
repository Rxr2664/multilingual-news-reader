from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, get_user_by_email
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import TokenOut, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google/url")
async def google_url():
    if not settings.google_client_id:
        raise HTTPException(400, "Google OAuth is not configured")
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return {"url": f"{GOOGLE_AUTH}?{urlencode(params)}"}


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(400, "Google OAuth is not configured")
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_res.raise_for_status()
        access = token_res.json()["access_token"]
        info_res = await client.get(
            GOOGLE_USERINFO, headers={"Authorization": f"Bearer {access}"}
        )
        info_res.raise_for_status()
        info = info_res.json()

    user = await get_user_by_email(db, info["email"])
    if user is None:
        user = User(
            google_sub=info.get("sub"),
            email=info["email"],
            name=info.get("name") or "",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token(user.id, user.email)
    from fastapi.responses import RedirectResponse

    resp = RedirectResponse(f"{settings.frontend_url}/auth/callback?token={token}")
    return resp


@router.post("/demo", response_model=TokenOut)
async def demo_login(email: str = "learner@example.com", db: AsyncSession = Depends(get_db)):
    if not settings.demo_login_enabled:
        raise HTTPException(403, "Demo login disabled")
    user = await get_user_by_email(db, email)
    if user is None:
        user = User(email=email, name="Demo Learner", google_sub=None)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id, user.email))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.target_language:
        user.target_language = payload.target_language
    if payload.target_country:
        user.target_country = payload.target_country
    await db.commit()
    await db.refresh(user)
    return user
