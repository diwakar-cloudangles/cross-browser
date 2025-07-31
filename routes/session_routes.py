# routes/session_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.session_service import SessionService
from database import BrowserType

router = APIRouter()

class CreateSessionRequest(BaseModel):
    browser_type: BrowserType

@router.post("/", response_model=dict)
async def create_session(request: CreateSessionRequest):
    """Create a new browser session"""
    try:
        session = await SessionService.create_session(
            browser_type=request.browser_type
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=dict)
async def get_session(session_id: str):
    """Get session details"""
    session = await SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}")
async def stop_session(session_id: str):
    """Stop a session"""
    success = await SessionService.stop_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be stopped")
    return {"message": "Session stopped successfully"}