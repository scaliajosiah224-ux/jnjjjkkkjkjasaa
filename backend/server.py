"""
RingRing API - Main FastAPI Application
Refactored modular structure with clean separation of concerns
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Import routers
from routes import auth, messages, voice, sinch_callbacks, numbers, contacts, calls, voicemail, webhooks, gifs
from routes.dependencies import get_current_user
from utils.websocket import ConnectionManager

load_dotenv()

# Configuration
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "ringring")

# Database client
db_client = None
db = None

# WebSocket manager
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global db_client, db
    # Startup
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.messages.create_index([("conversation_id", 1), ("created_at", -1)])
    await db.calls.create_index([("user_id", 1), ("created_at", -1)])
    
    print("✅ Database connected and indexes created")
    
    # Set WebSocket manager for routes that need it
    messages.set_ws_manager(manager)
    webhooks.set_ws_manager(manager)
    
    yield
    
    # Shutdown
    if db_client:
        db_client.close()
        print("❌ Database connection closed")

# Initialize FastAPI app
app = FastAPI(
    title="RingRing API",
    description="TextNow/Caddy Clone - Voice, Video, SMS/MMS Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(voice.router)
app.include_router(sinch_callbacks.router)
app.include_router(numbers.router)
app.include_router(contacts.router)
app.include_router(calls.router)
app.include_router(voicemail.router)
app.include_router(webhooks.router)
app.include_router(gifs.router)

# WebSocket endpoint
@app.websocket("/api/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket connection for real-time messaging"""
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            # Echo back or handle specific commands if needed
            await manager.send_to_user(user_id, {"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db_client else "disconnected"
    return {
        "status": "healthy",
        "service": "RingRing API",
        "version": "1.0.0",
        "database": db_status
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to RingRing API",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
