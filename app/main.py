from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.interview import router as interview_router
from app.api.matching import router as matching_router

app = FastAPI(
    title="介護事業所マッチングAPI",
    description="面接動画のAI解析結果をもとに、応募者に適した介護事業所タイプを判定します。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)
app.include_router(matching_router)


@app.get("/health")
def health():
    return {"status": "ok"}
