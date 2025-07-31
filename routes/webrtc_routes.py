# routes/webrtc_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from services.webrtc_service import WebRTCService
from services.session_service import SessionService

router = APIRouter()

class WebRTCOfferRequest(BaseModel):
    session_id: str
    offer: Dict[str, Any]

@router.post("/offer")
async def handle_webrtc_offer(request: WebRTCOfferRequest):
    """Handle WebRTC offer and return answer"""
    try:
        session = await SessionService.get_session(request.session_id)
        if not session or not session.get("vnc_port"):
            raise HTTPException(status_code=404, detail="Session not ready or not found")
        
        answer = await WebRTCService.handle_offer(
            request.session_id,
            request.offer,
            session["vnc_port"]
        )
        return answer
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))