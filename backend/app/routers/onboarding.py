from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import FrequencyWord, OnboardingSeedIn, UserOut
from app.services import vocab as vocab_svc

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

DATA = Path(__file__).resolve().parents[2] / "data"


def _load_freq(lang: str) -> list[str]:
    path = DATA / f"frequency_{lang}.txt"
    if not path.exists():
        path = DATA / "frequency_fr.txt"
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@router.get("/sample", response_model=list[FrequencyWord])
async def sample(user: User = Depends(get_current_user), limit: int = 80):
    words = _load_freq(user.target_language)[:limit]
    return [FrequencyWord(lemma=w, rank=i + 1) for i, w in enumerate(words)]


@router.post("/seed", response_model=UserOut)
async def seed(
    payload: OnboardingSeedIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await vocab_svc.bulk_import(db, user, payload.known, familiarity=3)
    user.onboarded = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
