"""The isolation chokepoint.

THIS IS THE ONLY MODULE ALLOWED TO QUERY QDRANT. Every search goes through
`search()`, which ALWAYS scopes to a single member's namespace. There is no
code path — and must never be one — that reads vectors without a namespace.
This is both the product's integrity guarantee and the demo's winning moment.

Two isolation modes (env ISOLATION_MODE):
  - "collection_per_member": one physical Qdrant collection per member. The
    stores are literally separate; the inspector can show that visually.
  - "single_collection": one collection, mandatory payload filter on namespace.
"""
from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings

_settings = get_settings()
_client = AsyncQdrantClient(url=_settings.qdrant_url)

_SINGLE = "family_memories"


def _collection_for(namespace: str) -> str:
    if _settings.isolation_mode == "collection_per_member":
        return f"mem_{namespace}"
    return _SINGLE


async def ensure_collection(namespace: str) -> None:
    name = _collection_for(namespace)
    existing = {c.name for c in (await _client.get_collections()).collections}
    if name not in existing:
        await _client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=_settings.embedding_dim, distance=models.Distance.COSINE
            ),
        )


async def upsert(namespace: str, member_id: str, memory_id: str, point_id: str,
                 vector: list[float], payload_extra: dict) -> None:
    await ensure_collection(namespace)
    payload = {
        "namespace": namespace,
        "member_id": member_id,
        "memory_id": memory_id,
        "status": "active",
        **payload_extra,
    }
    # wait=True makes the write durable before returning. Without it, a burst of
    # upserts (e.g. seeding 100+ memories while Qdrant is still warming up) can be
    # acknowledged but never applied, leaving memories that exist in Postgres but
    # are invisible to recall. Correctness over a few ms of latency.
    await _client.upsert(
        collection_name=_collection_for(namespace),
        points=[models.PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )


def _namespace_filter(namespace: str, active_only: bool) -> models.Filter:
    must = [models.FieldCondition(key="namespace", match=models.MatchValue(value=namespace))]
    if active_only:
        must.append(models.FieldCondition(key="status", match=models.MatchValue(value="active")))
    return models.Filter(must=must)


async def search(namespace: str, vector: list[float], limit: int,
                 active_only: bool = True) -> list[dict]:
    """The sole retrieval path. ALWAYS namespace-scoped.

    Even in collection-per-member mode (where the collection is already private)
    we still apply the namespace payload filter — defense in depth, and it keeps
    the guarantee identical across both modes.
    """
    await ensure_collection(namespace)
    hits = await _client.search(
        collection_name=_collection_for(namespace),
        query_vector=vector,
        query_filter=_namespace_filter(namespace, active_only),
        limit=limit,
        with_payload=True,
    )
    out = []
    for h in hits:
        # Hard assertion: a returned point must belong to this namespace. If this
        # ever fires, isolation is broken and we fail loudly rather than leak.
        assert h.payload and h.payload.get("namespace") == namespace, "ISOLATION BREACH"
        out.append({
            "memory_id": h.payload["memory_id"],
            "score": h.score,
            "kind": h.payload.get("kind"),
            "salience": h.payload.get("salience", 0.5),
        })
    return out


async def count(namespace: str, active_only: bool = False) -> int:
    """Number of points stored for a namespace. Namespace-scoped like everything here."""
    await ensure_collection(namespace)
    res = await _client.count(
        collection_name=_collection_for(namespace),
        count_filter=_namespace_filter(namespace, active_only),
        exact=True,
    )
    return res.count


async def existing_point_ids(namespace: str) -> set[str]:
    """All point IDs currently stored for a namespace (used by the seed self-heal
    to detect memories whose vector never landed). Namespace-scoped, no vectors read."""
    await ensure_collection(namespace)
    ids: set[str] = set()
    offset = None
    while True:
        points, offset = await _client.scroll(
            collection_name=_collection_for(namespace),
            scroll_filter=_namespace_filter(namespace, active_only=False),
            with_payload=False,
            with_vectors=False,
            limit=256,
            offset=offset,
        )
        ids.update(str(p.id) for p in points)
        if offset is None:
            break
    return ids


async def set_status(namespace: str, point_id: str, status: str) -> None:
    await _client.set_payload(
        collection_name=_collection_for(namespace),
        payload={"status": status},
        points=[point_id],
    )


async def delete_namespace(namespace: str) -> None:
    """Right-to-be-forgotten primitive: wipe a member's vectors."""
    name = _collection_for(namespace)
    if _settings.isolation_mode == "collection_per_member":
        try:
            await _client.delete_collection(collection_name=name)
        except Exception:
            pass
    else:
        await _client.delete(
            collection_name=name,
            points_selector=models.FilterSelector(filter=_namespace_filter(namespace, active_only=False)),
        )


def new_point_id() -> str:
    return str(uuid.uuid4())
