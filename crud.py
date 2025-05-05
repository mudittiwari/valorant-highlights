from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from models import User, Match, MatchInDB, UserCreate, MatchStatus
from database import db
from bson import ObjectId
from typing import Optional
from database import users_collection
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def str_id(id: ObjectId) -> str:
    return str(id)


# ✅testing done
async def get_user_by_email(email: str) -> Optional[User]:
    user = await users_collection.find_one({"email": email})
    # print(user)
    if user:
        user["_id"] = str(user["_id"])
        return User(**user)
    return None


# ✅testing done
async def create_user(user: UserCreate) -> User:
    try:
        hashed_password = pwd_context.hash(user.password)
        user_data = user.dict(exclude_unset=True, exclude={"id"})
        user_data["password"] = hashed_password
        result = await users_collection.insert_one(user_data)
        created_user = await users_collection.find_one({"_id": result.inserted_id})
        created_user["_id"] = str(created_user["_id"])
        return User(**created_user)
    
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


# ✅testing done
async def update_user_with_password(user_id: str, update_data: dict) -> User:
    update_data = update_data.dict(exclude_unset=True)
    try:
        if "password" in update_data:
            update_data["password"] = pwd_context.hash(update_data["password"])

        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found or no changes")

        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        return User(**updated_user)
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user with password")



# ✅testing done
async def create_match(match: Match) -> MatchInDB:
    match_dict = match.dict()
    result = await db.matches.insert_one(match_dict)
    created_match = await db.matches.find_one({"_id": result.inserted_id})
    created_match["id"] = str(created_match["_id"])
    user = await db.users.find_one({"email": match.user_id})
    if user:
        await db.users.update_one(
            {"email": match.user_id},
            {"$push": {"matches": str_id(created_match["_id"])}}
        )
    return MatchInDB(**created_match)


# ✅testing done
async def update_match_status(match_id: str, match_status: MatchStatus) -> str:
    created_match = await db.matches.find_one({"_id": ObjectId(match_id)})
    if not created_match:
        return "Match not found"
    await db.matches.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": {"status": match_status}}
    )
    print("Match status updated to " + match_status)
    return "Match status updated to " + match_status

# ✅testing done
async def update_match_zip_file(match_id: str, zip_file: str) -> str:
    created_match = await db.matches.find_one({"_id": ObjectId(match_id)})
    if not created_match:
        return "Match not found"
    await db.matches.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": {"zip_file_link": zip_file}}
    )
    print("Match status updated to " + zip_file)
    return "Match status updated to " + zip_file


# ✅testing done
async def get_user_matches(user_id: str) -> List[MatchInDB]:
    matches_cursor = db.matches.find({"user_id": user_id})
    matches = await matches_cursor.to_list(length=100)
    for match in matches:
        match["id"] = str(match["_id"])
    return [MatchInDB(**match) for match in matches]

async def link_match_to_user(user_id: str, match_id: str) -> User:
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"matches": match_id}}
    )
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return User(**user)


# ✅testing done
async def get_all_users() -> List[User]:
    users_cursor = db.users.find()
    users = await users_cursor.to_list(length=100)
    for user in users:
        user["_id"] = str(user["_id"])
    return [User(**user) for user in users]
