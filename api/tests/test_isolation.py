"""The guard test. It asserts the wall holds: across 100+ seeded memories spread
over multiple members, a query in member A's namespace never returns a memory id
belonging to member B.

This test is both the integrity guarantee and, exported, the "isolation
attestation" a customer's security review can rely on. Keep it green.

Run (with stack up + provider reachable):  pytest -q api/tests/test_isolation.py
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.memory import embeddings
from app.memory import qdrant_client as vec


@pytest.mark.asyncio
async def test_cross_member_isolation():
    ns_a = f"test_a_{uuid.uuid4().hex[:6]}"
    ns_b = f"test_b_{uuid.uuid4().hex[:6]}"
    await vec.ensure_collection(ns_a)
    await vec.ensure_collection(ns_b)

    a_ids, b_ids = set(), set()

    async def seed(ns: str, ids: set, texts: list[str]):
        for t in texts:
            v = await embeddings.embed(t)
            mid = str(uuid.uuid4())
            pid = vec.new_point_id()
            await vec.upsert(ns, "member", mid, pid, v, {"kind": "fact", "salience": 0.6})
            ids.add(mid)

    await seed(ns_a, a_ids, [f"Member A fact number {i} about topic {i%7}" for i in range(60)])
    await seed(ns_b, b_ids, [f"Member B fact number {i} about topic {i%7}" for i in range(60)])

    # query A's namespace with text deliberately similar to B's content
    for probe in ["fact about topic 3", "Member B fact number 10", "topic 5"]:
        qv = await embeddings.embed(probe)
        hits = await vec.search(ns_a, qv, limit=20)
        returned = {h["memory_id"] for h in hits}
        assert returned.issubset(a_ids), "ISOLATION BREACH: A's query returned non-A memories"
        assert returned.isdisjoint(b_ids), "ISOLATION BREACH: A's query returned B's memories"

    # cleanup
    await vec.delete_namespace(ns_a)
    await vec.delete_namespace(ns_b)


if __name__ == "__main__":
    asyncio.run(test_cross_member_isolation())
    print("isolation guard test passed")
