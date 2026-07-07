from __future__ import annotations

import random

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (
    AuditLog, Household, Member, Memory, Message, ProposedAction, Session, get_session,
)
from app.memory import embeddings
from app.memory import qdrant_client as vec

router = APIRouter(prefix="/api/demo", tags=["demo"])


class SeedIn(BaseModel):
    scenario: str = "legal"
    bulk_count: int = 110   # discovery volume on the litigation matter


# Each matter is an isolated principal (its own namespace). The first two are an
# ethical-wall pair: the firm sues Borealis for Acme AND separately advises Borealis,
# so the two teams must be screened from each other.
_MATTERS = [
    ("Acme Corp v. Borealis - Litigation", "matter", "litigation_assistant"),
    ("Borealis Ltd - Employment Counsel", "matter", "employment_assistant"),
    ("Vertex / Nimbus - M&A", "matter", "corporate_assistant"),
]

# High-salience privileged facts that must NEVER surface in another matter.
_PRIVILEGED_A = [
    ("fact", "Acme's board authorized a settlement ceiling of $4.2M in the Borealis litigation.", 0.97),
    ("fact", "Litigation strategy: move to exclude the Borealis email chain as hearsay before trial.", 0.92),
    ("relationship", "Dr. Lena Ortiz is Acme's lead expert witness; her deposition is set for next month.", 0.88),
    ("event", "Trial is scheduled to begin the first Monday of next quarter.", 0.75),
    ("fact", "Borealis is the opposing party in this litigation (note: the firm also advises Borealis on a separate, screened matter).", 0.7),
]

_BULK_A = [
    ("fact", "Bates-stamped document {} was produced in discovery."),
    ("task", "Review exhibit {} for privilege before production."),
    ("event", "Deposition of witness {} is on the discovery calendar."),
    ("relationship", "{} is listed as a fact witness in the matter."),
    ("fact", "Interrogatory response {} concerns the supply-contract timeline."),
]
_TOKENS = ["A-0{}".format(i) for i in range(10, 99)] + \
          ["Reyes", "Tan", "Okafor", "Mehta", "Nilsson", "Park", "Dubois", "Haddad",
           "Quinn", "Serrano", "Walsh", "Ibrahim", "Costa", "Lindqvist", "Yamada"]

_SEED_B = [
    ("fact", "The firm advises Borealis Ltd on employment matters, screened from the Acme litigation.", 0.85),
    ("fact", "Borealis updated its remote-work policy in Q1.", 0.5),
    ("task", "Draft a response to a Borealis employee grievance.", 0.6),
    ("event", "Borealis management training is scheduled for next month.", 0.4),
]

_SEED_C = [
    ("fact", "Vertex Holdings is acquiring Nimbus Systems; target close in Q3.", 0.75),
    ("fact", "Key deal term: a three-year earn-out tied to revenue.", 0.6),
    ("task", "Prepare the disclosure schedules for the Vertex acquisition.", 0.5),
    ("relationship", "Nimbus founders will remain for a 12-month transition.", 0.45),
]


async def _add(db: AsyncSession, member: Member, kind: str, content: str, salience: float) -> None:
    vector = await embeddings.embed(content)
    point_id = vec.new_point_id()
    row = Memory(member_id=member.id, namespace=member.memory_namespace, kind=kind,
                 content=content, salience=round(salience, 2), status="active",
                 qdrant_point_id=point_id)
    db.add(row)
    await db.flush()
    await vec.upsert(member.memory_namespace, str(member.id), str(row.id), point_id, vector,
                    payload_extra={"kind": kind, "salience": round(salience, 2)})


@router.post("/seed")
async def seed(body: SeedIn, db: AsyncSession = Depends(get_session)):
    # wipe prior demo data (vectors first, by namespace), then relational rows
    for m in (await db.execute(select(Member))).scalars().all():
        await vec.delete_namespace(m.memory_namespace)
    for table in (AuditLog, ProposedAction, Memory, Message, Session, Member, Household):
        await db.execute(delete(table))
    await db.commit()

    firm = Household(name="Demo Law Firm LLP")
    db.add(firm)
    await db.flush()

    created: list[Member] = []
    for name, role, persona in _MATTERS:
        # no memory_namespace passed — the model's secure default generates an
        # opaque crypto key on flush; the readable label stays in `name`.
        m = Member(household_id=firm.id, name=name, role=role, persona_key=persona)
        db.add(m)
        await db.flush()
        await vec.ensure_collection(m.memory_namespace)
        created.append(m)
    await db.commit()

    litigation, employment, corporate = created[0], created[1], created[2]

    # privileged facts + bulk discovery into the litigation matter (the wall + scale demo)
    for kind, content, sal in _PRIVILEGED_A:
        await _add(db, litigation, kind, content, sal)
    n = len(_PRIVILEGED_A)
    for _ in range(body.bulk_count):
        kind, tmpl = random.choice(_BULK_A)
        await _add(db, litigation, kind, tmpl.format(random.choice(_TOKENS)),
                   round(random.uniform(0.2, 0.7), 2))
        n += 1

    for kind, content, sal in _SEED_B:
        await _add(db, employment, kind, content, sal)
    for kind, content, sal in _SEED_C:
        await _add(db, corporate, kind, content, sal)
    await db.commit()

    # Self-heal: guarantee every stored memory has a live vector before returning.
    # Even with durable upserts this is the belt-and-suspenders that makes the seed
    # deterministic — any memory whose vector didn't land is re-embedded here, so
    # the demo can never come up half-indexed (the failure that hid the privileged
    # facts on first deploy).
    healed = 0
    for m in created:
        healed += await _heal_member(db, m)

    return {
        "firm": firm.name,
        "members": [{"id": str(m.id), "name": m.name, "role": m.role} for m in created],
        "bulk_member": litigation.name,
        "bulk_memories_created": n,
        "vectors_healed": healed,
        "wall_demo": "From the Borealis or Vertex matter, ask for Acme's settlement position - it returns nothing.",
    }


async def _heal_member(db: AsyncSession, member: Member) -> int:
    """Re-embed and re-upsert any active memory for this member that has no vector."""
    rows = (await db.execute(
        select(Memory).where(Memory.member_id == member.id, Memory.status == "active")
    )).scalars().all()
    present = await vec.existing_point_ids(member.memory_namespace)
    healed = 0
    for mem in rows:
        # qdrant_point_id comes back as a UUID object; Qdrant point IDs and the
        # scrolled set are strings, so normalize before comparing/upserting.
        pid = str(mem.qdrant_point_id)
        if pid in present:
            continue
        vector = await embeddings.embed(mem.content)
        await vec.upsert(member.memory_namespace, str(member.id), str(mem.id),
                         pid, vector,
                         payload_extra={"kind": mem.kind, "salience": float(mem.salience)})
        healed += 1
    return healed
