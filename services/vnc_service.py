# # services/vnc_service.py
# import asyncio
# from typing import Dict, Any
# from services.webrtc_service import vnc_clients
# # from Xlib.keysymdef import xkb as XK
# import Xlib.keysymdef.misc as misc_keys
# import Xlib.keysymdef.xkb as xkb_keys

# class VNCService:
#     @staticmethod
#     async def send_input(session_id: str, input_data: Dict[str, Any]):
#         """Send user input to the correct VNC server using asyncvnc."""
#         client = vnc_clients.get(session_id)
#         if not client:
#             return

#         try:
#             # THE FIX IS HERE: We wrap the operation in a try/except block
#             # This is more robust than checking the client's state.
#             input_type = input_data.get("input_type")
            
#             if input_type == "mouse":
#                 await VNCService._send_mouse_input(client, input_data)
#             elif input_type == "keyboard":
#                 print("Sending data..................................")
#                 await VNCService._send_keyboard_input(client, input_data)
        
#         except Exception:
#             # If the client is closed, an error will occur. We can safely ignore it.
#             pass

#     @staticmethod
#     async def _send_mouse_input(client: Any, data: Dict[str, Any]):
#         """Forward mouse events to VNC."""
#         x = data.get("x", 0)
#         y = data.get("y", 0)
#         button_code = data.get("button", 0)
#         button_mask = 1 << (button_code - 1) if button_code > 0 else 0

#         await client.pointer_event(x, y, button_mask)
        
#         if data.get("action") == "click":
#             await asyncio.sleep(0.05)
#             await client.pointer_event(x, y, 0)
#         # else: # For move
#         #     await client.pointer_event(x, y, 0)

#     # @staticmethod
#     # async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
#     #     """Forward keyboard events to VNC."""
#     #     key_str = data.get("key", "")
#     #     # if key_str:
#     #     #     await client.key_press(key_str)
#     #     if not key_str:
#     #         return

#     #     # VNC requires numeric keysyms, not characters.
#     #     # We use a library to convert the character to its keysym value.
#     #     # For special keys like 'Enter' or 'Shift', a mapping is needed.
        
#     #     keysym = None
#     #     if len(key_str) == 1:
#     #         keysym = XK.string_to_keysym(key_str)
#     #     else:
#     #         # Simple mapping for special keys
#     #         key_map = {
#     #             "Enter": XK.XK_Return,
#     #             "Backspace": XK.XK_BackSpace,
#     #             "Tab": XK.XK_Tab,
#     #             "Escape": XK.XK_Escape,
#     #             "ArrowUp": XK.XK_Up,
#     #             "ArrowDown": XK.XK_Down,
#     #             "ArrowLeft": XK.XK_Left,
#     #             "ArrowRight": XK.XK_Right,
#     #         }
#     #         keysym = key_map.get(key_str, None)

#     #     if keysym:
#     #         # We must simulate both pressing the key down and releasing it.
#     #         await client.key_down(keysym)
#     #         await client.key_up(keysym)

#     @staticmethod
#     async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
#         """Forward keyboard events to VNC."""
#         print(f"DEBUG: Processing keyboard input: {data}")
#         try:
#             key_str = data.get("key")
#             if not key_str:
#                 print("DEBUG: No key provided in input data, skipping keyboard input.")
#                 return

#             # Map for special keys from JavaScript's e.key to X11 keysyms
#             special_key_map = {
#                 "Enter": misc_keys.XK_Return, "Backspace": misc_keys.XK_BackSpace,
#                 "Tab": misc_keys.XK_Tab, "Escape": misc_keys.XK_Escape,
#                 "ArrowUp": misc_keys.XK_Up, "ArrowDown": misc_keys.XK_Down,
#                 "ArrowLeft": misc_keys.XK_Left, "ArrowRight": misc_keys.XK_Right,
#                 "Shift": misc_keys.XK_Shift_L, "Control": misc_keys.XK_Control_L,
#                 "Alt": misc_keys.XK_Alt_L,
#             }

#             keysym = special_key_map.get(key_str)
            
#             # If not a special key, convert the character to a keysym
#             if keysym is None and len(key_str) == 1:
#                 keysym = XK.string_to_keysym(key_str)

#             if keysym:
#                 # Simulate a full key press (down and up)
#                 print(f"DEBUG: Converted '{key_str}' to keysym '{keysym}'. Sending to VNC.")
#                 await client.key_down(keysym)
#                 await client.key_up(keysym)
#             else:
#                 print(f"Warning: Unhandled key '{key_str}'")
        
#         except Exception as e:
#             print(f"Error sending keyboard input to VNC: {e}")


# # services/vnc_service.py
# import asyncio
# from typing import Dict, Any
# from services.webrtc_service import vnc_clients

# # The py-xlib import is no longer needed for keyboard input
# # from Xlib import XK

# class VNCService:
#     @staticmethod
#     async def send_input(session_id: str, input_data: Dict[str, Any]):
#         """Send user input to the correct VNC server."""
#         client = vnc_clients.get(session_id)
#         if not client:
#             return

#         try:
#             if input_data.get("input_type") == "mouse":
#                 await VNCService._send_mouse_input(client, input_data)
#             elif input_data.get("input_type") == "keyboard":
#                 await VNCService._send_keyboard_input(client, input_data)
#         except Exception as e:
#             print(f"An exception occurred in send_input: {e}")

#     @staticmethod
#     async def _send_mouse_input(client: Any, data: Dict[str, Any]):
#         """Forward mouse events using the verified asyncvnc methods."""
#         x, y = data.get("x", 0), data.get("y", 0)
#         action, button_code = data.get("action"), data.get("button", 0)

#         if action == "move":
#             await client.mouse.move(x, y)
#         elif action == "click":
#             # Use the specific click methods based on the button code
#             if button_code == 1:  # Left click
#                 await client.mouse.click()
#             elif button_code == 2:  # Middle click
#                 await client.mouse.middle_click()
#             elif button_code == 3:  # Right click
#                 await client.mouse.right_click()

#     @staticmethod
#     async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
#         """Forward keyboard events by sending the key name as a string."""
#         try:
#             key_str = data.get("key")
#             if not key_str:
#                 return

#             # Map ambiguous browser key names to specific VNC key names
#             key_name_map = {
#                 "Shift": "Shift_L", "Control": "Control_L",
#                 "Alt": "Alt_L", "Meta": "Super_L", "Enter": "Return",
#                 "Backspace": "BackSpace", "Tab": "Tab", "Escape": "Escape",
#                 "ArrowUp": "Up", "ArrowDown": "Down",
#                 "ArrowLeft": "Left", "ArrowRight": "Right",
#             }
#             key_to_send = key_name_map.get(key_str, key_str)

#             # Pass the key name string directly to the press method
#             await client.keyboard.press(key_to_send)

#         except Exception as e:
#             print(f"Error processing keyboard input for key '{data.get('key')}': {e}")

# services/vnc_service.py
import asyncio
from typing import Dict, Any, List
from services.webrtc_service import vnc_clients

class VNCService:
    @staticmethod
    async def send_input(session_id: str, input_data: Dict[str, Any]):
        """Send user input to the correct VNC server."""
        client = vnc_clients.get(session_id)
        if not client:
            return

        try:
            if input_data.get("input_type") == "mouse":
                await VNCService._send_mouse_input(client, input_data)
            elif input_data.get("input_type") == "keyboard":
                await VNCService._send_keyboard_input(client, input_data)
        except Exception as e:
            print(f"An exception occurred in send_input: {e}")

    @staticmethod
    async def _send_mouse_input(client: Any, data: Dict[str, Any]):
        """Forward mouse events using the verified asyncvnc methods."""
        x, y = data.get("x", 0), data.get("y", 0)
        action, button_code = data.get("action"), data.get("button", 0)

        if action == "move":
            client.mouse.move(x, y)
        elif action == "click":
            if button_code == 1:
                client.mouse.click()
            elif button_code == 2:
                client.mouse.middle_click()
            elif button_code == 3:
                client.mouse.right_click()

        # --- ADD THIS BLOCK TO HANDLE SCROLLING ---
        elif action == "scroll":
            direction = data.get("direction")
            if direction == "up":
                client.mouse.scroll_up()
            elif direction == "down":
                client.mouse.scroll_down()
        # --- END OF NEW BLOCK ---

    @staticmethod
    async def _send_keyboard_input(client: Any, data: Dict[str, Any]):
        """
        Forward keyboard events, handling modifier keys for combinations.
        """
        try:
            key_str = data.get("key")
            # Get the list of active modifier keys from the frontend
            modifiers = data.get("modifiers", [])

            if not key_str:
                return

            # If the pressed key is itself a modifier, do nothing.
            # The frontend should only send events for non-modifier keys,
            # passing the active modifiers in the 'modifiers' list.
            if key_str in ["Shift", "Control", "Alt", "Meta"]:
                return

            key_name_map = {
                "Shift": "Shift_L", "Control": "Control_L",
                "Alt": "Alt_L", "Meta": "Super_L", "Enter": "Return",
                "Backspace": "BackSpace", "Tab": "Tab", "Escape": "Escape",
                "ArrowUp": "Up", "ArrowDown": "Down",
                "ArrowLeft": "Left", "ArrowRight": "Right",
            }

            # Map the modifier names from the frontend to the names VNC expects
            mapped_modifiers = [key_name_map.get(m, m) for m in modifiers if m in key_name_map]
            
            # Get the name of the main key to press
            key_to_press = key_name_map.get(key_str, key_str)

            # Use the 'hold' context manager to hold down modifiers
            with client.keyboard.hold(*mapped_modifiers):
                # Press the main key while modifiers are held
                client.keyboard.press(key_to_press)

        except Exception as e:
            print(f"Error processing keyboard input for key '{data.get('key')}': {e}")