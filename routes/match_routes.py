# app/routes/match_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models import Match, MatchInDB
from crud import create_match, get_user_matches, get_user_by_email
from dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=MatchInDB)
async def create_new_match(match: Match):
    user = await get_user_by_email(match.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")
    return await create_match(match)

@router.get("/currentuser", response_model=List[MatchInDB])
async def get_matches_for_user(current_user: dict = Depends(get_current_user)):
    return await get_user_matches(current_user["sub"])
