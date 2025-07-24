document.addEventListener('DOMContentLoaded', () => {
    const videoElement = document.getElementById('remote-video');
    const statusElement = document.getElementById('status');
    const overlay = document.getElementById('overlay');

    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');

    if (!sessionId) {
        statusElement.textContent = 'Error: No Session ID provided.';
        return;
    }

    const wsUrl = window.location.origin.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/${sessionId}`);
    
    let pc;

    const createPeerConnection = () => {
        pc = new RTCPeerConnection({
            iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        });

        pc.ontrack = (event) => {
            if (videoElement.srcObject !== event.streams[0]) {
                videoElement.srcObject = event.streams[0];
                overlay.style.display = 'none';
            }
        };

        pc.onconnectionstatechange = () => {
            statusElement.textContent = `Status: ${pc.connectionState}`;
            if (pc.connectionState === 'connected') {
                overlay.style.display = 'none';
            } else if (['disconnected', 'failed', 'closed'].includes(pc.connectionState)) {
                overlay.style.display = 'flex';
                overlay.innerHTML = '<p>Connection lost. Please try again.</p>';
            }
        };
    };

    ws.onopen = async () => {
        statusElement.textContent = 'Status: Handshaking...';
        createPeerConnection();

        try {
            const offer = await pc.createOffer({ offerToReceiveVideo: true });
            await pc.setLocalDescription(offer);

            ws.send(JSON.stringify({
                type: 'webrtc_offer',
                data: { offer: { sdp: offer.sdp, type: offer.type } }
            }));
        } catch (error) {
            console.error('Error creating WebRTC offer:', error);
        }
    };

    ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'webrtc_answer') {
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(message.data));
            } catch (e) {
                console.error('Error setting remote description:', e);
            }
        }
    };

    ws.onerror = (error) => {
        statusElement.textContent = 'Error: WebSocket connection failed.';
        overlay.style.display = 'flex';
        overlay.innerHTML = '<p>Could not connect to the server.</p>';
    };

    ws.onclose = () => {
        if (pc && pc.connectionState !== 'closed') {
            pc.close();
        }
    };
    
    const sendInput = (payload) => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'input', data: payload }));
        }
    };
    
    const getMousePosition = (event) => {
        const rect = videoElement.getBoundingClientRect();
        const x = Math.round(event.clientX - rect.left);
        const y = Math.round(event.clientY - rect.top);
        return { x, y };
    };

    videoElement.addEventListener('mousemove', (e) => {
        const { x, y } = getMousePosition(e);
        sendInput({ input_type: 'mouse', action: 'move', x, y });
    });

    videoElement.addEventListener('mousedown', (e) => {
        e.preventDefault();
        const { x, y } = getMousePosition(e);
        sendInput({ input_type: 'mouse', action: 'click', button: e.button + 1, x, y });
    });
    
    videoElement.addEventListener('contextmenu', e => e.preventDefault());

    document.addEventListener('keydown', (e) => {
        e.preventDefault();
        sendInput({ input_type: 'keyboard', action: 'press', key: e.key });
    });
});