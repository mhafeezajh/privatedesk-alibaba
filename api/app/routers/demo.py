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
    scenario: str = "legal"       # "legal" | "healthcare"
    bulk_count: int = 110         # volume on the high-scale principal (discovery / visit history)


# ── LEGAL scenario ───────────────────────────────────────────────────────────
# Each matter is an isolated principal. The first two are an ethical-wall pair: the
# firm sues Borealis for Acme AND separately advises Borealis, so they must be screened.
_LEGAL_A = [  # high-salience privileged facts that must NEVER surface in another matter
    ("fact", "Acme's board authorized a settlement ceiling of $4.2M in the Borealis litigation.", 0.97),
    ("fact", "Litigation strategy: move to exclude the Borealis email chain as hearsay before trial.", 0.92),
    ("relationship", "Dr. Lena Ortiz is Acme's lead expert witness; her deposition is set for next month.", 0.88),
    ("event", "Trial is scheduled to begin the first Monday of next quarter.", 0.75),
    ("fact", "Borealis is the opposing party in this litigation (note: the firm also advises Borealis on a separate, screened matter).", 0.7),
]
_LEGAL_B = [
    ("fact", "The firm advises Borealis Ltd on employment matters, screened from the Acme litigation.", 0.85),
    ("fact", "Borealis updated its remote-work policy in Q1.", 0.5),
    ("task", "Draft a response to a Borealis employee grievance.", 0.6),
    ("event", "Borealis management training is scheduled for next month.", 0.4),
]
_LEGAL_C = [
    ("fact", "Vertex Holdings is acquiring Nimbus Systems; target close in Q3.", 0.75),
    ("fact", "Key deal term: a three-year earn-out tied to revenue.", 0.6),
    ("task", "Prepare the disclosure schedules for the Vertex acquisition.", 0.5),
    ("relationship", "Nimbus founders will remain for a 12-month transition.", 0.45),
]
_LEGAL_BULK = [
    ("fact", "Bates-stamped document {} was produced in discovery."),
    ("task", "Review exhibit {} for privilege before production."),
    ("event", "Deposition of witness {} is on the discovery calendar."),
    ("relationship", "{} is listed as a fact witness in the matter."),
    ("fact", "Interrogatory response {} concerns the supply-contract timeline."),
]
_LEGAL_TOKENS = ["A-0{}".format(i) for i in range(10, 99)] + \
    ["Reyes", "Tan", "Okafor", "Mehta", "Nilsson", "Park", "Dubois", "Haddad",
     "Quinn", "Serrano", "Walsh", "Ibrahim", "Costa", "Lindqvist", "Yamada"]

# ── HEALTHCARE scenario ──────────────────────────────────────────────────────
# Same engine; the principal is a PATIENT and the wall is patient confidentiality.
_HEALTH_A = [  # confidential facts that must NEVER surface for another patient
    ("fact", "Maria Delgado is HIV-positive; her status is strictly confidential and must not be disclosed without written consent.", 0.97),
    ("fact", "Maria is prescribed Truvada; medication adherence is reviewed at monthly check-ins.", 0.9),
    ("relationship", "Maria's primary care physician is Dr. Aisha Rahman.", 0.85),
    ("event", "Maria's next appointment is the first Monday of next month.", 0.75),
    ("fact", "Maria has a documented sulfa drug allergy.", 0.7),
]
_HEALTH_B = [
    ("fact", "James Okoro had a drug-eluting stent placed in the LAD in Q1.", 0.85),
    ("fact", "James is on dual antiplatelet therapy: aspirin plus clopidogrel.", 0.6),
    ("relationship", "James's cardiologist is Dr. Lin Wei.", 0.55),
    ("event", "James's next stress test is scheduled for next month.", 0.4),
]
_HEALTH_C = [
    ("fact", "Sofia Marin (age 7) has a documented penicillin allergy.", 0.9),
    ("fact", "Sofia's immunizations are up to date as of her last visit.", 0.5),
    ("relationship", "Sofia's parent and legal guardian is Elena Marin.", 0.55),
    ("task", "Schedule Sofia's annual well-child visit.", 0.4),
]
_HEALTH_BULK = [
    ("event", "Clinic visit {} recorded routine follow-up notes."),
    ("fact", "Lab result {} filed: values within normal range."),
    ("event", "Vitals recorded at visit {}: blood pressure and weight stable."),
    ("task", "Medication refill {} was processed at the pharmacy."),
    ("fact", "Progress note {} documents symptom review and care plan."),
]
_HEALTH_TOKENS = ["V-0{}".format(i) for i in range(10, 99)] + \
    ["Jan-12", "Feb-03", "Mar-19", "Apr-08", "May-21", "Jun-02",
     "Jul-15", "Aug-09", "Sep-27", "Oct-11", "Nov-05", "Dec-18"]

# Scenario registry: org name, principals (name, role, persona, facts, is_bulk_target),
# and the bulk templates/tokens for the high-scale principal.
_SCENARIOS: dict[str, dict] = {
    "legal": {
        "org": "Demo Law Firm LLP",
        "principals": [
            ("Acme Corp v. Borealis - Litigation", "matter", "litigation_assistant", _LEGAL_A, True),
            ("Borealis Ltd - Employment Counsel", "matter", "employment_assistant", _LEGAL_B, False),
            ("Vertex / Nimbus - M&A", "matter", "corporate_assistant", _LEGAL_C, False),
        ],
        "bulk_templates": _LEGAL_BULK,
        "bulk_tokens": _LEGAL_TOKENS,
        "wall_demo": "From the Borealis or Vertex matter, ask for Acme's settlement position — it returns nothing.",
    },
    "healthcare": {
        "org": "Evergreen Family Health",
        "principals": [
            ("Maria Delgado - Primary Care", "patient", "primary_care_assistant", _HEALTH_A, True),
            ("James Okoro - Cardiology", "patient", "cardiology_assistant", _HEALTH_B, False),
            ("Sofia Marin - Pediatrics", "patient", "pediatric_assistant", _HEALTH_C, False),
        ],
        "bulk_templates": _HEALTH_BULK,
        "bulk_tokens": _HEALTH_TOKENS,
        "wall_demo": "From James's or Sofia's chart, ask for Maria's HIV status — it returns nothing.",
    },
}


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
    scenario = _SCENARIOS.get(body.scenario, _SCENARIOS["legal"])

    # wipe prior demo data (vectors first, by namespace), then relational rows
    for m in (await db.execute(select(Member))).scalars().all():
        await vec.delete_namespace(m.memory_namespace)
    for table in (AuditLog, ProposedAction, Memory, Message, Session, Member, Household):
        await db.execute(delete(table))
    await db.commit()

    org = Household(name=scenario["org"])
    db.add(org)
    await db.flush()

    # create each principal; no memory_namespace passed — the model's secure default
    # mints an opaque crypto key on flush; the readable label stays in `name`.
    created: list[Member] = []
    for name, role, persona, _facts, _bulk in scenario["principals"]:
        m = Member(household_id=org.id, name=name, role=role, persona_key=persona)
        db.add(m)
        await db.flush()
        await vec.ensure_collection(m.memory_namespace)
        created.append(m)
    await db.commit()

    # seed each principal's facts; the bulk-target principal also gets high-volume
    # background memories (the needle-in-a-haystack / bounded-recall demo).
    n = 0
    bulk_member = created[0]
    templates, tokens = scenario["bulk_templates"], scenario["bulk_tokens"]
    for member, (_n, _r, _p, facts, is_bulk) in zip(created, scenario["principals"]):
        for kind, content, sal in facts:
            await _add(db, member, kind, content, sal)
            n += 1
        if is_bulk:
            bulk_member = member
            for _ in range(body.bulk_count):
                kind, tmpl = random.choice(templates)
                await _add(db, member, kind, tmpl.format(random.choice(tokens)),
                           round(random.uniform(0.2, 0.7), 2))
                n += 1
    await db.commit()

    # Self-heal: guarantee every stored memory has a live vector before returning.
    # Belt-and-suspenders on top of durable upserts — any memory whose vector didn't
    # land is re-embedded here, so the demo can never come up half-indexed.
    healed = 0
    for m in created:
        healed += await _heal_member(db, m)

    return {
        "scenario": body.scenario if body.scenario in _SCENARIOS else "legal",
        "org": org.name,
        "members": [{"id": str(m.id), "name": m.name, "role": m.role} for m in created],
        "bulk_member": bulk_member.name,
        "bulk_memories_created": n,
        "vectors_healed": healed,
        "wall_demo": scenario["wall_demo"],
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
