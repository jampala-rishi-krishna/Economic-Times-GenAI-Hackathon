"""
NEXUS — Agentic Meeting Intelligence Platform
FastAPI Application Entry Point
"""
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()
from services.email_service import email_service
print(f"[EMAIL CONFIG] Address: {email_service.sender_email or 'NOT SET ❌'}")
print(f"[EMAIL CONFIG] Password: {'SET ✅' if email_service.app_password else 'NOT SET ❌'}")
print(f"[EMAIL CONFIG] Enabled: {email_service.enabled}")

# ─── Database Setup ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Startup: create tables + seed sample data ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Seed sample data in DEMO_MODE
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        await seed_sample_data()

    print("\n" + "="*60)
    print("  🚀 NEXUS is running — open http://localhost:5173")
    print("  📡 API Docs: http://localhost:8000/docs")
    print("  🔌 WebSocket: ws://localhost:8000/ws/workflow/{meeting_id}")
    print("="*60 + "\n")

    yield


async def seed_sample_data():
    """Seed the sample Q4 strategy meeting and run the full workflow."""
    db = SessionLocal()
    try:
        from database import crud
        from crews.flow import SAMPLE_TRANSCRIPT, run_meeting_workflow

        # Check if already seeded
        existing = crud.get_meetings(db, limit=1)
        if existing:
            print("ℹ️  Sample data already seeded — skipping")
            return

        print("🌱 Seeding sample data...")

        meeting = crud.create_meeting(
            db=db,
            title="Q4 Product Strategy Meeting",
            raw_transcript=SAMPLE_TRANSCRIPT,
            participants=["Sarah", "James", "Priya", "Marcus"],
            duration_minutes=45
        )

        print(f"   Created meeting: {meeting.id}")
        print("   Running NEXUS autonomous workflow...")

        await run_meeting_workflow(db, meeting.id, demo_mode=False)
        print("✅ Sample data seeded successfully!")

    except Exception as e:
        print(f"⚠️  Sample data seeding failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="NEXUS — Agentic Meeting Intelligence Platform",
    description="Autonomous Enterprise Workflow Intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ─────────────────────────────────────────────────────────
from routers import meetings, tasks, audit, workflow, system

app.include_router(meetings.router)
app.include_router(tasks.router)
app.include_router(audit.router)
app.include_router(workflow.router)
app.include_router(system.router)

# Dashboard stats — alias
@app.get("/api/dashboard/stats")
async def dashboard_stats(db: Session = Depends(get_db)):
    from database import crud
    return crud.get_dashboard_stats(db)

# ─── WebSocket ───────────────────────────────────────────────────────────────
from websocket_manager import manager


@app.websocket("/ws/workflow/{meeting_id}")
async def websocket_meeting(websocket: WebSocket, meeting_id: str):
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            # Keep connection alive; receive any client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)


@app.websocket("/ws/global")
async def websocket_global(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/test-email")
async def test_email(to: str = "rishikrishnajampala@gmail.com"):
    from services.email_service import email_service
    print(f"[EMAIL CONFIG] Address: {email_service.sender_email or 'NOT SET ❌'}")
    print(f"[EMAIL CONFIG] Password: {'SET ✅' if email_service.app_password else 'NOT SET ❌'}")
    print(f"[EMAIL CONFIG] Enabled: {email_service.enabled}")
    
    if not email_service.enabled:
        return {
            "status": "disabled",
            "reason": "GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in .env",
            "gmail_address_set": bool(email_service.sender_email),
            "app_password_set": bool(email_service.app_password)
        }
    
    result = email_service.send_email(
        to_email=to,
        subject="[NEXUS] ✅ Email Test — It's Working!",
        html_content=email_service._get_base_html("""
            <h2>NEXUS Email Test ✅</h2>
            <p>If you received this, your Gmail SMTP is configured correctly.</p>
            <p>Emails will now be sent automatically when workflows run.</p>
        """)
    )
    
    return {
        "status": "sent" if result else "failed",
        "to": to,
        "gmail_configured": True
    }


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "NEXUS", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
