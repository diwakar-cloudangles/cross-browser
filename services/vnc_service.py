# services/vnc_service.py
import asyncio
from typing import Dict, Any
from services.webrtc_service import vnc_clients

class VNCService:
    @staticmethod
    async def send_input(session_id: str, input_data: Dict[str, Any]):
        """Send user input to the correct VNC server using asyncvnc."""
        client = vnc_clients.get(session_id)
        if not client or client.closed:
            return

        try:
            input_type = input_data.get("input_type")
            
            if input_type == "mouse":
                await VNCService._send_mouse_input(client, input_data)
            elif input_type == "keyboard":
                await VNCService._send_keyboard_input(client, input_data)
                
        except Exception as e:
            print(f"Error sending VNC input via asyncvnc for session {session_id}: {e}")

    @staticmethod
    async def _send_mouse_input(client: Any, data: Dict[str, Any]):
        """Forward mouse events to VNC."""
        x = data.get("x", 0)
        y = data.get("y", 0)
        button_code = data.get("button", 0)
        
        # asyncvnc uses a bitmask for buttons. 1=left, 2=middle, 4=right
        button_mask = 1 << (button_code - 1) if button_code > 0 else 0
        
        # For a click, we do a quick press and release. For move, mask is 0.
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