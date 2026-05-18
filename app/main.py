from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db
from app.api.matching import router as matching_router
from app.api.records import router as records_router
from app.api.health import router as health_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="介護事業所マッチングAPI",
    description="Zoom録画 → NotebookLM テキスト → 事業所適性判定 → DB保存",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(matching_router)
app.include_router(records_router)
app.include_router(health_router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}
