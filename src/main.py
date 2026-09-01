from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.moves import router as moves_router
from src.api.v1.reports import router as reports_router

app = FastAPI(
    title="OmniLedger",
    version="0.1.0",
    description="Standalone Accounting & General Ledger Service for OmniFlow SaaS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "omniledger-standalone"}


app.include_router(moves_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")