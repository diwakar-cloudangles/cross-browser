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
        # self._task = asyncio.create_task(self._connect_vnc())
        try:
            self._vnc_task = asyncio.create_task(self._run_vnc_client())
        except Exception as e:
            print("Error: ",{e})

    async def _run_vnc_client(self):
        try:
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    print(f"VNC connection attempt {attempt + 1}/{max_retries}...")
                    
                    # Step 1: Connect WITHOUT the pixel_format argument.
                    self.vnc_context = asyncvnc.connect(
                        'host.docker.internal', self.vnc_port, password='password'
                    )
                    # self.vnc_context = asyncvnc.connect(
                    #     '127.0.0.1', self.vnc_port, password='password'
                    # )
                    self.client = await self.vnc_context.__aenter__()

                    # Step 2: Set the pixel format on the client object AFTER connecting.
                    self.client.pixel_format = 'rgb888'

                    print("VNC connection successful and pixel format set.")
                    break  # Exit the retry loop on success
                
                except Exception as e:
                    print(f"VNC connection failed on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        print("All VNC connection attempts failed. Cleaning up.")
                        return  # End the task if all retries fail
                    await asyncio.sleep(1) # Wait 1 second before retrying
            vnc_clients[self.session_id] = self.client
            print(f"Successfully connected via asyncvnc for session {self.session_id}")
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"VNC client run error for session {self.session_id}: {e}")
        finally:
            print(f"Cleaning up VNC connection for session {self.session_id}")
            if self.session_id in vnc_clients:
                vnc_clients.pop(self.session_id, None)
            if self.vnc_context:
                await self.vnc_context.__aexit__(None, None, None)
            self.client = None
            self.vnc_context = None

    def stop(self):
        """Synchronously called by aiortc to stop the track."""
        if hasattr(self, '_vnc_task') and not self._vnc_task.done():
            asyncio.create_task(self._cancel_vnc_task())

    async def _cancel_vnc_task(self):
        """Helper to safely cancel the VNC connection task."""
        self._vnc_task.cancel()
        try:
            await self._vnc_task
        except asyncio.CancelledError:
            pass # Cancellation is expected.

    async def recv(self) -> VideoFrame:
        # THE FIX IS HERE: We remove the explicit check for a closed client
        # and rely on the try/except block below.
        if not self.client:
            await asyncio.sleep(1/30)
            return VideoFrame.from_ndarray(np.zeros((720, 1280, 3), dtype=np.uint8), format="rgb24")
        try:
            rgba_array = await self.client.screenshot()
            # rgb_array = rgba_array[:, :, :3]
            # frame_array = np.array(pil_image.convert("RGB"))
            frame = VideoFrame.from_ndarray(rgb_array, format="rgb24")
            frame.pts, frame.time_base = self._timestamp, 1000
            self._timestamp += 33
            return frame
        except Exception as e:
            print(f"Error capturing VNC screen with asyncvnc for session {self.session_id}: {e}")
            await self._cancel_vnc_task()
            return VideoFrame.from_ndarray(np.zeros((720, 1280, 3), dtype=np.uint8), format="rgb24")

class WebRTCService:
    peer_connections: Dict[str, RTCPeerConnection] = {}
    @staticmethod
    async def create_peer_connection(session_id: str, vnc_port: int, manager: Any) -> RTCPeerConnection:
        ice_servers = [
            RTCIceServer(urls="stun:stun.l.google.com:19302"),
            RTCIceServer(
                urls=[
                    "turns:global.relay.metered.ca:443?transport=tcp"
                ],
                username="<23273cca1e4f8db06759aad4>",
                credential="3J46gFT7HHYj+ly1",
            ),
        ]
        configuration = RTCConfiguration(iceServers=ice_servers)
        # configuration = RTCConfiguration(iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")])
        pc = RTCPeerConnection(configuration=configuration)
        WebRTCService.peer_connections[session_id] = pc
        video_track = VNCVideoTrack(vnc_port, session_id)
        pc.addTrack(video_track)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"Connection state for {session_id} is {pc.connectionState}")
            if pc.connectionState in ["failed", "closed", "disconnected"]:
                await video_track._cancel_vnc_task(); await WebRTCService.cleanup_peer_connection(session_id)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                print(f"Sending ICE candidate to client {session_id}: {candidate.to_dict()}")
                await manager.send_message(session_id, {
                    "type": "webrtc_ice_candidate",
                    "data": candidate.to_dict()
                })

        return pc

    @staticmethod
    async def handle_offer(session_id: str, offer: dict, vnc_port: int, manager: Any) -> dict:
        try:
            pc = await WebRTCService.create_peer_connection(session_id, vnc_port, manager)
            
            # offer_data = offer.get("offer", {});
            # if not offer_data.get("sdp") or not offer_data.get("type"): raise ValueError("Invalid offer format")
            # await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"]))
            # answer = await pc.createAnswer()
            # await pc.setLocalDescription(answer)
            # return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

            offer_details = offer
            
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_details["sdp"], type=offer_details["type"]))
            
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        except Exception as e:
            print(f"Error handling WebRTC offer for session {session_id}: {e}"); await WebRTCService.cleanup_peer_connection(session_id); raise e

    @staticmethod
    async def add_ice_candidate(session_id: str, candidate_data: dict):
        if session_id in WebRTCService.peer_connections:
            pc = WebRTCService.peer_connections[session_id]
            # aiortc expects an RTCIceCandidate object, not a dict
            from aiortc.sdp import candidate_from_sdp
            
            # The candidate from JS is a dictionary, format it for aiortc
            cand = candidate_from_sdp(candidate_data.get("candidate", ""))
            cand.sdpMid = candidate_data.get("sdpMid")
            cand.sdpMLineIndex = candidate_data.get("sdpMLineIndex")
            
            print(f"Adding ICE candidate for session {session_id}: {cand}")
            await pc.addIceCandidate(cand)
        else:
            print(f"Warning: Peer connection for session {session_id} not found when adding ICE candidate.")
            
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
