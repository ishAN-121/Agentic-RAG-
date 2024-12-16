import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from pymongo import MongoClient
from dotenv import load_dotenv
from backend.main_backend import QueryRequest
from mongo.general.functions import add_chat_to_conversation, create_conversation
from mongo.general.schema import PyMongoConversation
from agent import run_pipeline

# from common.evaluator import EnhancedRAGPipeline
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


try:
    client = MongoClient(os.environ["MONGO_CONNECTION_STRING"])
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as e:
    print("Failed to connect to MongoDB:", e)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_conversation(websocket: WebSocket, request: QueryRequest):
    db = client["sirius"]
    conversations_collection = db["Message"]
    print(request)

    try:
        if not request.id or request.id.strip() == "":
            conversation_data = {
                "title": request.query,
                "chats": [{"message": request.query, "role": "USER", "order": 1}],
            }
            new_conversation = PyMongoConversation.model_validate(conversation_data)
            result = create_conversation(client, new_conversation)
            inserted_conversation = conversations_collection.find_one(
                {"_id": result.inserted_id}
            )

            await websocket.send_json(
                {
                    "type": "request",
                    "conversation": inserted_conversation,
                }
            )
            await asyncio.sleep(0.5)

            rag_response = run_pipeline(request.query)
            print(rag_response)

            updated_conversation = add_chat_to_conversation(
                client,
                str(inserted_conversation["_id"]),
                rag_response,
                "RAG",
            )

            await websocket.send_json(
                {
                    "type": "response",
                    "conversation": {
                        "id": str(updated_conversation["_id"]),
                        "title": updated_conversation["title"],
                        "chats": updated_conversation["chats"],
                    },
                }
            )

        else:
            rag_response = run_pipeline(request.query)
            from swarm.util import debug_print

            debug_print(True, f"Processing tree call: Final RAG Response")
            assistant_msg = add_chat_to_conversation(client, request.id, rag_response)
            print(assistant_msg)
            await websocket.send_json({"type": "response", "message": assistant_msg})

    except Exception as e:
        print(f"Conversation handling error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


@app.websocket("/ws/query")
async def query_websocket_handler(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request = QueryRequest.model_validate_json(data)
            await handle_conversation(websocket, request)
    except WebSocketDisconnect:
        print("Query WebSocket disconnected")
    except Exception as e:
        print(f"Query WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5050)
