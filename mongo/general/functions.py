import datetime
from typing import Literal
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, timezone
from mongo.general.schema import PyMongoConversation


def create_conversation(client: MongoClient, conversation: PyMongoConversation):
    db = client["conversationdb"]
    conversations_collection = db["conversations"]
    conversation_dict = conversation.model_dump(by_alias=True)
    return conversations_collection.insert_one(conversation_dict)


def add_chat_to_conversation(
    client: MongoClient,
    chatId: str,
    content: str,
    role="ASSISTANT",
) -> dict:
    db = client["sirius"]
    message_collection = db["Message"]
    current_time = datetime.now(timezone.utc)

    # Format the time string
    response = message_collection.insert_one(
        {
            "chatId": ObjectId(chatId),
            "content": content,
            "role": role,
            "createdAt": datetime.now(tz=timezone.utc),
        }
    )
    new_created_doc = message_collection.find_one({"_id": response.inserted_id})
    chat_response = {
        "id": str(new_created_doc["_id"]),
        "chatId": str(new_created_doc["chatId"]),
        "role": new_created_doc["role"],
        "content": new_created_doc["content"],
        "createdAt": str(new_created_doc["createdAt"]),
    }
    print(chat_response)
    return chat_response
