from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from auth import verify_access_token
from models import ProcessRequest
from models import Match, MatchStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ✅testing done
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return payload 


# ✅testing done
def create_match_from_request(req: ProcessRequest, user_id: str) -> Match:
    return Match(
        link=req.youtube_url,
        players=req.player_names,
        zip_file_link="",
        user_id=user_id,
        status=MatchStatus.in_queue)