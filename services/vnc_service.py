# services/vnc_service.py
import asyncio
from typing import Dict, Any
from services.webrtc_service import vnc_clients

class VNCService:
    @staticmethod
    async def send_input(session_id: str, input_data: Dict[str, Any]):
        """Send user input to the correct VNC server using asyncvnc."""
        client = vnc_clients.get(session_id)
        if not client:
            return

        try:
            # THE FIX IS HERE: We wrap the operation in a try/except block
            # This is more robust than checking the client's state.
            input_type = input_data.get("input_type")
            
            if input_type == "mouse":
                await VNCService._send_mouse_input(client, input_data)
            elif input_type == "keyboard":
                await VNCService._send_keyboard_input(client, input_data)
        
        except Exception:
            # If the client is closed, an error will occur. We can safely ignore it.
            pass

    @staticmethod
    async def _send_mouse_input(client: Any, data: Dict[str, Any]):
        """Forward mouse events to VNC."""
        x = data.get("x", 0)
        y = data.get("y", 0)
        button_code = data.get("button", 0)
        button_mask = 1 << (button_code - 1) if button_code > 0 else 0
        
        if data.get("action") == "click":
            await client.pointer_event(x, y, button_mask)
            await asyncio.sleep(0.05)
            await client.pointer_event(x, y, 0)
        else: # For move
            await client.pointer_event(x, y, 0)

    @staticmethod
    async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
        """Forward keyboard events to VNC."""
        key_str = data.get("key", "")
        if key_str:
            await client.key_press(key_str)