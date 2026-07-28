import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure search paths for clean imports
# Trigger reload: update to gemini-3.1-flash-lite

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

sys.path.append(str(ROOT_DIR))
sys.path.append(str(BACKEND_DIR))

# Import mock sub-routers
from routes.chat import router as chat_router
from routes.navigation import router as navigation_router
from routes.crowd import router as crowd_router
from routes.transport import router as transport_router
from routes.staff import router as staff_router
from routes.sustainability import router as sustainability_router
from routes.accessibility import router as accessibility_router

# Import RAG database loaders
from ai_service import list_venues

@asynccontextmanager
async def lifespan(app: FastAPI):
    venues = list_venues()
    n = len(venues)
    print(f"StadiumAI backend ready — {n} venues loaded")
    yield

app = FastAPI(title="StadiumAI Backend", lifespan=lifespan)

# Setup CORS middleware according to constraints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Associate endpoint routers for both /api/... and root /... prefixes
app.include_router(chat_router, prefix="/api/chat")
app.include_router(chat_router, prefix="/chat")

app.include_router(navigation_router, prefix="/api/navigation")
app.include_router(navigation_router, prefix="/navigation")

app.include_router(crowd_router, prefix="/api/crowd")
app.include_router(crowd_router, prefix="/crowd")

app.include_router(transport_router, prefix="/api/transport")
app.include_router(transport_router, prefix="/transport")

app.include_router(staff_router, prefix="/api/staff")
app.include_router(staff_router, prefix="/staff")

app.include_router(sustainability_router, prefix="/api/sustainability")
app.include_router(sustainability_router, prefix="/sustainability")

app.include_router(accessibility_router, prefix="/api/accessibility")
app.include_router(accessibility_router, prefix="/accessibility")



@app.get("/health")
def health_endpoint():
    venues = list_venues()
    return {"status": "ok", "venue_count": len(venues)}

@app.get("/venues")
def get_venues_endpoint():
    return list_venues()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
