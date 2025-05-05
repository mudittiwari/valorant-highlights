from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from enum import Enum


class ProcessRequest(BaseModel):
    youtube_url: str
    start_time: str
    end_time: str
    player_names: list[str]
    email: str

class MatchStatus(str, Enum):
    in_queue = "in_queue"
    successfully_done = "successfully_done"
    failed = "failed"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    password: Optional[str] = None

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    city: str
    country: str
    state: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(alias="_id")
    matches: List[str] = []
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class Match(BaseModel):
    link: str
    players: List[str]
    zip_file_link: str
    user_id: str
    status: MatchStatus

class MatchInDB(Match):
    id: str 

    class Config:
        orm_mode = True
