# services/webrtc_service.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from typing import Dict, Any
import numpy as np
from av import VideoFrame
import asyncvnc

vnc_clients: Dict[str, any] = {}

class VNCVideoTrack(VideoStreamTrack):
    def __init__(self, vnc_port: int, session_id: str):
        super().__init__()
        self.vnc_port, self.session_id, self.client, self.vnc_context, self._timestamp = vnc_port, session_id, None, None, 0
        self._task = asyncio.create_task(self._connect_vnc())

    async def _connect_vnc(self):
        try:
            self.vnc_context = asyncvnc.connect('127.0.0.1', self.vnc_port, password='password')
            self.client = await self.vnc_context.__aenter__()
            vnc_clients[self.session_id] = self.client
            print(f"Successfully connected via asyncvnc for session {self.session_id}")
        except Exception as e:
            print(f"asyncvnc connection error for session {self.session_id}: {e}")
            if self.vnc_context: await self.vnc_context.__aexit__(None, None, None)
            self.client, self.vnc_context = None, None

    async def recv(self) -> VideoFrame:
        # THE FIX IS HERE: We remove the explicit check for a closed client
        # and rely on the try/except block below.
        if not self.client:
            await asyncio.sleep(1/30)
            return VideoFrame.from_ndarray(np.zeros((720, 1280, 3), dtype=np.uint8), format="rgb24")
        try:
            pil_image = await self.client.capture_screen()
            frame_array = np.array(pil_image.convert("RGB"))
            frame = VideoFrame.from_ndarray(frame_array, format="rgb24")
            frame.pts, frame.time_base = self._timestamp, 1000
            self._timestamp += 33
            return frame
        except Exception as e:
            print(f"Error capturing VNC screen with asyncvnc for session {self.session_id}: {e}")
            await self.stop()
            return VideoFrame.from_ndarray(np.zeros((720, 1280, 3), dtype=np.uint8), format="rgb24")

    async def stop(self):
        if self.session_id in vnc_clients: vnc_clients.pop(self.session_id)
        if self.vnc_context: await self.vnc_context.__aexit__(None, None, None); self.vnc_context = None
        self.client = None
        if self._task: self._task.cancel()

class WebRTCService:
    peer_connections: Dict[str, RTCPeerConnection] = {}
    @staticmethod
    async def create_peer_connection(session_id: str, vnc_port: int) -> RTCPeerConnection:
        ice_servers = [
            RTCIceServer(urls="stun:stun.relay.metered.ca:80"),
            RTCIceServer(urls="turn:global.relay.metered.ca:80", username="9a093fd7fc48f361fa9767f4", credential="pJnJrnGjsCIvp6zg"),
            RTCIceServer(urls="turn:global.relay.metered.ca:80?transport=tcp", username="9a093fd7fc48f361fa9767f4", credential="pJnJrnGjsCIvp6zg"),
            RTCIceServer(urls="turn:global.relay.metered.ca:443", username="9a093fd7fc48f361fa9767f4", credential="pJnJrnGjsCIvp6zg"),
            RTCIceServer(urls="turns:global.relay.metered.ca:443?transport=tcp", username="9a093fd7fc48f361fa9767f4", credential="pJnJrnGjsCIvp6zg"),

        ]
        configuration = RTCConfiguration(iceServers=ice_servers)
        pc = RTCPeerConnection(configuration=configuration)
        WebRTCService.peer_connections[session_id] = pc
        video_track = VNCVideoTrack(vnc_port, session_id)
        pc.addTrack(video_track)
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"Connection state for {session_id} is {pc.connectionState}")
            if pc.connectionState in ["failed", "closed", "disconnected"]:
                await video_track.stop(); await WebRTCService.cleanup_peer_connection(session_id)
        return pc
    @staticmethod
    async def handle_offer(session_id: str, offer: dict, vnc_port: int) -> dict:
        try:
            pc = await WebRTCService.create_peer_connection(session_id, vnc_port)
            offer_data = offer.get("offer", {});
            if not offer_data.get("sdp") or not offer_data.get("type"): raise ValueError("Invalid offer format")
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"]))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        except Exception as e:
            print(f"Error handling WebRTC offer for session {session_id}: {e}"); await WebRTCService.cleanup_peer_connection(session_id); raise e
    @staticmethod
    async def cleanup_peer_connection(session_id: str):
        if session_id in WebRTCService.peer_connections:
            pc = WebRTCService.peer_connections.pop(session_id); await pc.close()
        if session_id in vnc_clients:
            client = vnc_clients.pop(session_id)
            try:
                client.close()
            except Exception:
                pass # Ignore errors if client is already closed