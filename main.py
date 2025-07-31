# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json

from database import init_db
from routes import session_routes, webrtc_routes, container_routes
from services.container_service import ContainerService
from services.webrtc_service import WebRTCService
from routes.webrtc_routes import WebRTCOfferRequest

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    scheduler.start()
    
    scheduler.add_job(
        ContainerService.cleanup_expired_containers,
        'interval',
        minutes=30,
        id='cleanup_containers'
    )
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    await ContainerService.cleanup_all_containers()

app = FastAPI(title="Cross-Browser Testing Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(session_routes.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(webrtc_routes.router, prefix="/api/webrtc", tags=["webrtc"])
app.include_router(container_routes.router, prefix="/api/containers", tags=["containers"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()

# async def handle_websocket_message(session_id: str, data: dict):
#     message_type = data.get("type")
#     payload = data.get("data", {})
#     try:
#         if message_type == "input":
#             await ContainerService.forward_input(session_id, payload)
#         elif message_type == "webrtc_offer":
#             request_obj = WebRTCOfferRequest(session_id=session_id, offer=payload)
#             response = await webrtc_routes.handle_webrtc_offer(request_obj)
#             await manager.send_message(session_id, {"type": "webrtc_answer", "data": response})
#         elif message_type == "webrtc_ice_candidate":
#             await WebRTCService.add_ice_candidate(session_id, payload)
#         else:
#             print(f"Unknown message type: {message_type}")
#     except Exception as e:
#         print(f"Error handling websocket message for {session_id}: {e}")

# @app.websocket("/ws/{session_id}")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     await manager.connect(websocket, session_id)
#     try:
#         while True:
#             message = await websocket.receive_json()
#             await handle_websocket_message(session_id, message)
#     except WebSocketDisconnect:
#         print(f"WebSocket {session_id} disconnected.")
#     except Exception as e:
#         print(f"Error in websocket for {session_id}: {e}")
#     finally:
#         await WebRTCService.cleanup_peer_connection(session_id)
#         manager.disconnect(session_id)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    # Get session details to find the VNC port
    from services.session_service import SessionService
    session = await SessionService.get_session(session_id)
    if not session or not session.get("vnc_port"):
        print(f"Session {session_id} not found or not ready.")
        await websocket.close(code=1008)
        return

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            payload = data.get("data", {})
            print("came here 2 : ",payload)
            if message_type == "webrtc_offer":
                print(session_id)
                offer = payload.get("offer")
                if offer:
                    # Directly call the service and pass the manager
                    answer = await WebRTCService.handle_offer(
                        session_id=session_id,
                        offer=offer,
                        vnc_port=session["vnc_port"],
                        manager=manager  # Pass the manager instance
                    )
                    await manager.send_message(session_id, {"type": "webrtc_answer", "data": answer})
            
            elif message_type == "webrtc_ice_candidate":
                if payload:
                    await WebRTCService.add_ice_candidate(session_id, payload)

            elif message_type == "input":
                # Assuming you have this service function
                from services.vnc_service import VNCService
                await VNCService.send_input(session_id, payload)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        print(f"Error in WebSocket for session {session_id}: {e}")
    finally:
        await WebRTCService.cleanup_peer_connection(session_id)
        manager.disconnect(session_id)