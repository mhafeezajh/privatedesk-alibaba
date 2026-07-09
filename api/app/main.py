from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import describe, get_settings
from app.db import init_db
from app.llm import client
from app.memory import embeddings
from app.routers import actions, auth, chat, demo, inspector, members


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="PrivateDesk MemoryAgent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

for r in (auth.router, chat.router, members.router, inspector.router, actions.router, demo.router):
    app.include_router(r)


@app.get("/health")
async def health():
    """Proves the configured provider (Qwen Cloud or Ollama) is actually reachable:
    one tiny completion + one embedding."""
    info = describe()
    try:
        reply = await client.complete(
            [{"role": "user", "content": "Reply with the single word: ok"}]
        )
        vec = await embeddings.embed("healthcheck")
        info.update({"llm_ok": "ok" in reply.lower(), "embedding_dim_live": len(vec)})
    except Exception as e:  # noqa: BLE001
        info.update({"llm_ok": False, "error": str(e)})
    return info


@app.get("/")
async def root():
    s = get_settings()
    return {"service": "PrivateDesk MemoryAgent", "provider": s.provider_label}
