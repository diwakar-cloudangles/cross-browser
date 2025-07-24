# services/session_service.py
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update

from database import async_session_maker, Session, BrowserType, SessionStatus
from services.container_service import ContainerService

class SessionService:
    @staticmethod
    async def create_session(browser_type: BrowserType) -> dict:
        """Create a new browser session"""
        session_id = str(uuid.uuid4())
        
        async with async_session_maker() as db:
            session = Session(
                id=session_id,
                browser_type=browser_type,
                status=SessionStatus.PENDING,
            )
            db.add(session)
            await db.commit()
            
            try:
                container_info = await ContainerService.create_container(session_id, browser_type)
                
                return {
                    "session_id": session_id,
                    "browser_type": browser_type.value,
                    "status": "running",
                    "vnc_port": container_info["vnc_port"]
                }
            except Exception as e:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(status=SessionStatus.ERROR)
                )
                await db.commit()
                raise e
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        """Get session by ID"""
        async with async_session_maker() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                return {
                    "session_id": session.id,
                    "browser_type": session.browser_type.value,
                    "status": session.status.value,
                    "vnc_port": session.vnc_port
                }
            return None
    
    @staticmethod
    async def stop_session(session_id: str) -> bool:
        """Stop a session"""
        stopped = await ContainerService.stop_container(session_id)
        if stopped:
            async with async_session_maker() as db:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(status=SessionStatus.STOPPED)
                )
                await db.commit()
        return stopped
    
    @staticmethod
    async def list_sessions() -> List[dict]:
        """List all sessions"""
        async with async_session_maker() as db:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return [
                {
                    "session_id": session.id,
                    "browser_type": session.browser_type.value,
                    "status": session.status.value,
                    "created_at": session.created_at.isoformat()
                }
                for session in sessions
            ]