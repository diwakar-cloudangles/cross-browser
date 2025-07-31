# routes/container_routes.py
from fastapi import APIRouter, HTTPException
router = APIRouter()

@router.get("/{session_id}/stats")
async def get_container_stats(session_id: str):
    # This is a placeholder implementation
    return {
        "cpu_usage": "N/A",
        "memory_usage": "N/A",
    }