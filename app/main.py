from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.matching import router as matching_router

app = FastAPI(
    title="介護事業所マッチングAPI",
    description="面接動画をAIで解析したテキストデータと希望条件から、適した介護事業所タイプを判定します。",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matching_router)


@app.get("/health")
def health():
    return {"status": "ok"}
