# services/vnc_service.py
import asyncio
from typing import Dict, Any
from services.webrtc_service import vnc_clients
from Xlib.keysymdef import xkb as XK

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

        await client.pointer_event(x, y, button_mask)
        
        if data.get("action") == "click":
            await asyncio.sleep(0.05)
            await client.pointer_event(x, y, 0)
        # else: # For move
        #     await client.pointer_event(x, y, 0)

    # @staticmethod
    # async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
    #     """Forward keyboard events to VNC."""
    #     key_str = data.get("key", "")
    #     # if key_str:
    #     #     await client.key_press(key_str)
    #     if not key_str:
    #         return

    #     # VNC requires numeric keysyms, not characters.
    #     # We use a library to convert the character to its keysym value.
    #     # For special keys like 'Enter' or 'Shift', a mapping is needed.
        
    #     keysym = None
    #     if len(key_str) == 1:
    #         keysym = XK.string_to_keysym(key_str)
    #     else:
    #         # Simple mapping for special keys
    #         key_map = {
    #             "Enter": XK.XK_Return,
    #             "Backspace": XK.XK_BackSpace,
    #             "Tab": XK.XK_Tab,
    #             "Escape": XK.XK_Escape,
    #             "ArrowUp": XK.XK_Up,
    #             "ArrowDown": XK.XK_Down,
    #             "ArrowLeft": XK.XK_Left,
    #             "ArrowRight": XK.XK_Right,
    #         }
    #         keysym = key_map.get(key_str, None)

    #     if keysym:
    #         # We must simulate both pressing the key down and releasing it.
    #         await client.key_down(keysym)
    #         await client.key_up(keysym)

    @staticmethod
    async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
        """Forward keyboard events to VNC."""
        key_str = data.get("key")
        if not key_str:
            return

        # Map for special keys from JavaScript's e.key to X11 keysyms
        special_key_map = {
            "Enter": XK.XK_Return, "Backspace": XK.XK_BackSpace, "Tab": XK.XK_Tab,
            "Escape": XK.XK_Escape, "ArrowUp": XK.XK_Up, "ArrowDown": XK.XK_Down,
            "ArrowLeft": XK.XK_Left, "ArrowRight": XK.XK_Right, "Shift": XK.XK_Shift_L,
            "Control": XK.XK_Control_L, "Alt": XK.XK_Alt_L,
        }

        keysym = special_key_map.get(key_str)
        
        # If not a special key, convert the character to a keysym
        if keysym is None and len(key_str) == 1:
            keysym = XK.string_to_keysym(key_str)

        if keysym:
            # Simulate a full key press (down and up)
            await client.key_down(keysym)
            await client.key_up(keysym)
        else:
            print(f"Warning: Unhandled key '{key_str}'")
