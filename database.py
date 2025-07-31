import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, Boolean
from datetime import datetime
import enum

DATABASE_URL =os.getenv("DATABASE_URL", "mysql+pymysql://root:Root!123@host.docker.internal:3306/local_db")

# DATABASE_URL =os.getenv("DATABASE_URL", "mysql+pymysql://root:Root!123@localhost:3306/local_db")


# Convert to async URL
async_url = DATABASE_URL.replace("mysql+pymysql://", "mysql+aiomysql://")

engine = create_async_engine(async_url, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class BrowserType(enum.Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"

class SessionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True)
    browser_type = Column(Enum(BrowserType), nullable=False)
    container_id = Column(String(64), nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)
    vnc_port = Column(Integer, nullable=True)
    webrtc_offer = Column(Text, nullable=True)
    webrtc_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

class Container(Base):
    __tablename__ = "containers"
    
    id = Column(String(64), primary_key=True)
    session_id = Column(String(36), nullable=False)
    browser_type = Column(Enum(BrowserType), nullable=False)
    status = Column(String(20), default="creating")
    vnc_port = Column(Integer, nullable=False)
    cpu_usage = Column(Integer, default=0)
    memory_usage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_health_check = Column(DateTime, default=datetime.utcnow)

class BrowserConfig(Base):
    __tablename__ = "browser_configs"
    
    id = Column(Integer, primary_key=True)
    browser_type = Column(Enum(BrowserType), nullable=False)
    version = Column(String(20), nullable=False)
    docker_image = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    resource_limits = Column(Text, nullable=True)  # JSON string

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with async_session_maker() as session:
        yield session
