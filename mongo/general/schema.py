from pymongo import MongoClient
from typing import List, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class PyMongoChat(BaseModel):
    message: str
    role: Literal["USER", "RAG"]
    order: int


class PyMongoConversation(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    title: str
    chats: List[PyMongoChat]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
