"""Central configuration.

The deployment path is chosen by ONE rule: if DASHSCOPE_API_KEY is set we run
the Qwen Cloud path; if it is empty we fall back to the local Ollama config.
Nothing else in the codebase branches on cloud-vs-local — this is the single
seam that makes "same architecture, two deployments" true.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _b(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    # resolved LLM/embedding config (already collapsed to one path)
    is_cloud: bool
    llm_base_url: str
    llm_api_key: str
    reasoning_model: str
    headline_model: str
    embedding_model: str
    embedding_dim: int

    # infra
    postgres_dsn: str
    qdrant_url: str
    redis_url: str

    # memory engine
    k_candidates: int
    k_context: int
    dedup_threshold: float
    supersede_scan_floor: float
    salience_prune_floor: float
    w_sim: float
    w_sal: float
    w_rec: float
    isolation_mode: str  # "collection_per_member" | "single_collection"

    # app
    session_secret: str
    app_env: str
    prompt_cache_mode: str  # "partitioned" | "off" | "shared"

    @property
    def provider_label(self) -> str:
        return "Qwen Cloud (DashScope)" if self.is_cloud else "Local (Ollama)"


@lru_cache
def get_settings() -> Settings:
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    is_cloud = bool(dashscope_key)

    if is_cloud:
        llm_base_url = _b("LLM_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        api_key = dashscope_key
        reasoning = _b("LLM_REASONING_MODEL", "dashscope/qwen-plus")
        headline = _b("LLM_HEADLINE_MODEL", "dashscope/qwen3-max")
        embed = _b("EMBEDDING_MODEL", "dashscope/text-embedding-v4")
        embed_dim = int(_b("EMBEDDING_DIM", "1024"))
    else:
        llm_base_url = _b("LOCAL_LLM_BASE_URL", "http://host.docker.internal:11434/v1")
        api_key = "ollama"  # Ollama ignores the key but the OpenAI client needs one
        reasoning = _b("LOCAL_LLM_REASONING_MODEL", "ollama/qwen3:8b")
        headline = _b("LOCAL_LLM_HEADLINE_MODEL", "ollama/qwen3:32b")
        embed = _b("LOCAL_EMBEDDING_MODEL", "ollama/nomic-embed-text")
        embed_dim = int(_b("LOCAL_EMBEDDING_DIM", "768"))

    return Settings(
        is_cloud=is_cloud,
        llm_base_url=llm_base_url,
        llm_api_key=api_key,
        reasoning_model=reasoning,
        headline_model=headline,
        embedding_model=embed,
        embedding_dim=embed_dim,
        postgres_dsn=_b("POSTGRES_DSN", "postgresql+asyncpg://privatedesk:privatedesk@postgres:5432/privatedesk"),
        qdrant_url=_b("QDRANT_URL", "http://qdrant:6333"),
        redis_url=_b("REDIS_URL", "redis://redis:6379/0"),
        k_candidates=int(_b("K_CANDIDATES", "20")),
        k_context=int(_b("K_CONTEXT", "6")),
        dedup_threshold=float(_b("DEDUP_THRESHOLD", "0.92")),
        supersede_scan_floor=float(_b("SUPERSEDE_SCAN_FLOOR", "0.60")),
        salience_prune_floor=float(_b("SALIENCE_PRUNE_FLOOR", "0.2")),
        w_sim=float(_b("RERANK_W_SIM", "0.6")),
        w_sal=float(_b("RERANK_W_SAL", "0.25")),
        w_rec=float(_b("RERANK_W_REC", "0.15")),
        isolation_mode=_b("ISOLATION_MODE", "collection_per_member"),
        session_secret=_b("SESSION_SECRET", "change-me-in-prod"),
        app_env=_b("APP_ENV", "dev"),
        prompt_cache_mode=_b("PROMPT_CACHE_MODE", "partitioned"),
    )


def describe() -> dict:
    """Small, import-safe summary used by /health and the inspector header."""
    s = get_settings()
    return {
        "provider": s.provider_label,
        "is_cloud": s.is_cloud,
        "reasoning_model": s.reasoning_model,
        "embedding_model": s.embedding_model,
        "embedding_dim": s.embedding_dim,
        "isolation_mode": s.isolation_mode,
        "k_candidates": s.k_candidates,
        "k_context": s.k_context,
        "prompt_cache_mode": s.prompt_cache_mode,
    }
