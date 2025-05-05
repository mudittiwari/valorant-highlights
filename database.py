from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

MONGO_URI = "mongodb+srv://mudittiwari:itsmebro@cluster0.uzfeq.mongodb.net/"
DATABASE_NAME = "valorant-highlights"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

users_collection = db["users"]
matches_collection = db["matches"]