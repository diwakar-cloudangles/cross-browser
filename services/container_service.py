# services/container_service.py
import docker
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select, update, delete
import os

from database import async_session_maker, Container, Session, BrowserType, SessionStatus
from services.vnc_service import VNCService

class ContainerService:
    client = docker.from_env()

    @staticmethod
    async def _perform_vnc_health_check(port: int, retries: int = 10, delay: float = 1.5):
        """
        Actively checks if the VNC port on the host is ready.
        """
        print(f"Performing health check on host port {port}...")
        for attempt in range(retries):
            try:
                # Try to open a connection to the VNC port
                reader, writer = await asyncio.open_connection('host.docker.internal', port)

                # If connection succeeds, close it immediately and return
                writer.close()
                await writer.wait_closed()
                print(f"Health check successful on attempt {attempt + 1}. Container is ready.")
                return
            except ConnectionRefusedError:
                # This is expected if the service isn't ready yet
                print(f"Health check attempt {attempt + 1} failed. Retrying in {delay}s...")
                if attempt == retries - 1:
                    # If this was the last attempt, break the loop to raise an error
                    break
                await asyncio.sleep(delay)
            except Exception as e:
                # Handle other potential errors
                print(f"An unexpected error occurred during health check: {e}")
                break

        # If the loop finishes without returning, all retries have failed
        raise TimeoutError(f"Container failed to become healthy on port {port} after {retries} attempts.")

    @staticmethod
    async def create_container(session_id: str, browser_type: BrowserType) -> Dict[str, Any]:
        """Create and start a new browser container"""
        
        # Hardcoding port 5900 to remove any variables
        vnc_port = 5900
        # network_name = os.getenv("NETWORK_NAME", "cross-browser_app-network")
        
        container_config = {
            "image": f"browser-{browser_type.value}:latest",
            "name": f"browser-{session_id}",
            "ports": {
                # '5900/tcp': vnc_port
                '5900/tcp': None
            },
            # "network": network_name,
            "network": "bridge",
            "environment": {
                'VNC_PASSWORD': 'password'
            },
            "mem_limit": "2g",
            "cpu_period": 100000,
            "cpu_quota": 50000,
            "detach": True,
            "remove": True
        }
        
        try:
            # Running the blocking docker call in a separate thread
            container = await asyncio.to_thread(
                ContainerService.client.containers.run, **container_config
            )
            
            # Inspect the container to get the randomly assigned port
            container.reload()
            assigned_port = container.ports['5900/tcp'][0]['HostPort']

            # await asyncio.sleep(15)
            await ContainerService._perform_vnc_health_check(assigned_port)
            
            async with async_session_maker() as db:
                db_container = Container(
                    id=container.id,
                    session_id=session_id,
                    browser_type=browser_type,
                    status="running",
                    vnc_port=assigned_port,
                    created_at=datetime.utcnow()
                )
                db.add(db_container)
                
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(
                        container_id=container.id,
                        vnc_port=assigned_port,
                        status=SessionStatus.RUNNING
                    )
                )
                await db.commit()
            
            return {
                "container_id": container.id,
                # "vnc_port": vnc_port,
                "vnc_port": assigned_port,
                "status": "running"
            }
            
        except Exception as e:
            async with async_session_maker() as db:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(status=SessionStatus.ERROR)
                )
                await db.commit()
            
            raise Exception(f"Failed to create container: {str(e)}")

    @staticmethod
    async def stop_container(session_id: str) -> bool:
        """Stop and remove container"""
        try:
            container = ContainerService.client.containers.get(f"browser-{session_id}")
            container.stop()
            return True
        except docker.errors.NotFound:
            print(f"Container for session {session_id} not found, maybe already stopped.")
            return True # If it doesn't exist, it's stopped.
        except Exception as e:
            print(f"Error stopping container: {e}")
            return False

    @staticmethod
    async def forward_input(session_id: str, input_data: Dict[str, Any]):
        """Forward user input to container via VNC"""
        try:
            await VNCService.send_input(session_id, input_data)
            async with async_session_maker() as db:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(last_activity=datetime.utcnow())
                )
                await db.commit()
        except Exception as e:
            print(f"Error forwarding input: {e}")

    @staticmethod
    async def cleanup_expired_containers():
        """Cleanup expired containers (scheduled task)"""
        async with async_session_maker() as db:
            expired_time = datetime.utcnow() - timedelta(hours=1)
            result = await db.execute(
                select(Session).where(
                    Session.last_activity < expired_time,
                    Session.status == SessionStatus.RUNNING
                )
            )
            expired_sessions = result.scalars().all()
            for session in expired_sessions:
                print(f"Cleaning up expired session: {session.id}")
                await ContainerService.stop_container(session.id)
                session.status = SessionStatus.STOPPED
            await db.commit()

    @staticmethod
    async def cleanup_all_containers():
        """Cleanup all browser containers on shutdown"""
        try:
            for container in ContainerService.client.containers.list(filters={"name": "browser-*"}):
                container.stop()
        except Exception as e:
            print(f"Error during shutdown cleanup: {e}")