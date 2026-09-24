from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import BulkImportIn, KnowWordIn, UserOut
from app.services import vocab as vocab_svc

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.post("/know", response_model=UserOut)
async def know_word(
    payload: KnowWordIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await vocab_svc.mark_known(db, user, payload.lemma, payload.familiarity)
    return user


@router.post("/unknown")
async def unknown_word(
    payload: KnowWordIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await vocab_svc.mark_unknown(db, user, payload.lemma)
    return {"ok": True}


@router.post("/bulk", response_model=UserOut)
async def bulk_import(
    payload: BulkImportIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await vocab_svc.bulk_import(db, user, payload.lemmas, payload.familiarity)
    return user
