import os
import re
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()


async def monitor_logs(websocket: WebSocket, log_path: str):
    try:
        with open(log_path, "r") as file:
            file.seek(0, 2)
            while True:
                line = file.readline()
                if line:
                    match = re.search(r"Processing tool call: (\w+)", line)
                    tree_match = re.search(r"\[.*\] Processing tree call: (.+)", line)

                    if tree_match:
                        tree_name = tree_match.group(1).strip()
                        print(f"Sending tree log: {tree_name}")
                        await websocket.send_json({"type": "tree", "name": tree_name})
                else:
                    await asyncio.sleep(0.5)
    except Exception as e:
        print(f"Log monitoring error: {e}")
        await websocket.close()


@app.websocket("/ws/logs")
async def logs_websocket_handler(websocket: WebSocket):
    await websocket.accept()
    log_path = os.path.expanduser("~/swarm.log")
    try:
        await monitor_logs(websocket, log_path)
    except WebSocketDisconnect:
        print("Logs WebSocket disconnected")
    except Exception as e:
        print(f"Logs WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=6060)
