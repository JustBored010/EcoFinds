from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="MongoDB FastAPI", description="Simple API to read users from MongoDB")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)
# MongoDB connection - use localhost for local development
# Docker networking uses 'mongodb' as hostname, localhost for local development
IS_DOCKER = os.environ.get('IS_DOCKER', False)
MONGO_HOST = "mongodb" if IS_DOCKER else "localhost"
MONGO_URL = f"mongodb://root:example@{MONGO_HOST}:27017"
DATABASE_NAME = "mydb"
COLLECTION_NAME = "users"

# Connect to MongoDB
client = None

@app.on_event("startup")
async def startup_db_client():
    global client
    client = AsyncIOMotorClient(MONGO_URL)
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

# Model for User
class User(BaseModel):
    name: str
    email: Optional[str] = None
    password: str

class Cards(BaseModel):
    CardholderName:str
    CardNumber:str
    ExpiryDate:str
    CVV:str
    
# API Routes
@app.get("/")
def read_root():
    return {"message": "MongoDB FastAPI Service"}


@app.get("/users", response_model=List[dict])
async def get_all_users():
    users = []
    cursor = client[DATABASE_NAME][COLLECTION_NAME].find()
    async for document in cursor:
        # Convert ObjectId to string for JSON serialization
        document["_id"] = str(document["_id"])
        users.append(document)
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    from bson.objectid import ObjectId
    try:
        user = await client[DATABASE_NAME][COLLECTION_NAME].find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            return user
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    except:
        raise HTTPException(status_code=400, detail=f"Invalid user ID format")

@app.post("/users", response_model=dict)
async def create_user(user: User):
    
    new_user = await client[DATABASE_NAME][COLLECTION_NAME].insert_one(user.dict())
    created_user = await client[DATABASE_NAME][COLLECTION_NAME].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    return created_user

@app.post("/cards", response_model=dict)
async def card(card: Cards):
    
    new_user = await client[DATABASE_NAME][COLLECTION_NAME].insert_one(card.dict())
    created_user = await client[DATABASE_NAME][COLLECTION_NAME].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    return created_user

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)