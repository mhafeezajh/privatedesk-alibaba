# Proof-of-Deployment Clip — Backend running on Alibaba Cloud

A short, **separate** recording (target **60–90 seconds**, no hard limit) that proves the
backend runs on Alibaba Cloud and calls Qwen Cloud. This is **not** the 3-minute demo — keep it
factual and evidence-focused. Screen recording + optional voiceover.

**Goal:** a judge watching this is convinced the app is genuinely deployed on Alibaba Cloud ECS,
in Singapore, calling Qwen Cloud (DashScope) — not on your laptop.

---

## Pre-flight

- [ ] **Start the box** — it's kept stopped to avoid charges: `make infra-start` (same IP, ~1–2 min).
      The console must show it **Running** for this clip. `make infra-stop` afterwards.
- [ ] Log in to the **Alibaba Cloud console** in a browser (ECS → Instances, Singapore region).
- [ ] Have a terminal ready with the SSH key: `infra/terraform/generated/privatedesk.pem`.
- [ ] Confirm the box is healthy: `curl http://47.236.30.110:8000/health` → `"llm_ok": true`.
- [ ] Full-screen, ~125% zoom so IPs and JSON are legible.

---

## Shot list

### Shot 1 (0:00–0:20) — The ECS instance in the Alibaba console
| | |
|---|---|
| **On screen** | Alibaba Cloud **ECS → Instances**, Singapore (`ap-southeast-1`). Show the `privatedesk-api` instance **Running**, its **type** (`ecs.u1-c1m4.large`), and its **public/EIP `47.236.30.110`**. Hover the region selector so "Singapore" is visible. |
| **Say** | "The backend runs on an Alibaba Cloud ECS instance in the Singapore region — here it is, running, with elastic IP 47.236.30.110." |

### Shot 2 (0:20–0:30) — Networking (optional but strong)
| | |
|---|---|
| **On screen** | The instance's **Security Group** rules: inbound only **22, 3000, 8000**; and the **EIP** association. |
| **Say** | "Only the app and API ports are open; the databases stay private on the internal network." |

### Shot 3 (0:30–0:55) — Live on the box: containers + identity
| | |
|---|---|
| **On screen** | Terminal, run these against the ECS box: |

```bash
ssh -i infra/terraform/generated/privatedesk.pem root@47.236.30.110

# on the box — prove it's the ECS host and the stack is up:
curl -s http://100.100.100.200/latest/meta-data/region-id; echo     # → ap-southeast-1 (ECS metadata)
curl -s http://100.100.100.200/latest/meta-data/instance-id; echo   # → i-... (ECS instance id)
docker compose ps                                                   # postgres, qdrant, redis, api, web — all Up
```

| | |
|---|---|
| **Say** | "SSH'd into that instance — the Alibaba ECS metadata service confirms the region and instance ID, and all five containers of the stack are up: Postgres, Qdrant, Redis, the API, and the web app." |

> The `100.100.100.200` metadata endpoint is Alibaba Cloud's internal ECS metadata service — it
> only answers *from inside* an ECS instance, which is itself proof of where you are.

### Shot 4 (0:55–1:15) — Proof it's calling Qwen Cloud
| | |
|---|---|
| **On screen** | Still on the box (or from your laptop against the public IP): |

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```
Point at the output:
```json
{
  "provider": "Qwen Cloud (DashScope)",
  "is_cloud": true,
  "reasoning_model": "dashscope/qwen-plus",
  "embedding_model": "dashscope/text-embedding-v4",
  "embedding_dim_live": 1024,
  "llm_ok": true
}
```

| | |
|---|---|
| **Say** | "And `/health` does a real round-trip: one live completion and one live embedding against Qwen Cloud — DashScope — returning `llm_ok: true`. So the Alibaba-hosted backend is actively using Qwen Cloud's models." |

### Shot 5 (1:15–1:30) — The code that uses Alibaba Cloud (tie to repo)
| | |
|---|---|
| **On screen** | Open [`api/app/llm/client.py`](../api/app/llm/client.py) and [`api/app/config.py`](../api/app/config.py) (the `dashscope-intl.aliyuncs.com` endpoint), then flash [`infra/terraform/compute.tf`](../infra/terraform/compute.tf). |
| **Say** | "In the repo: this is where every model call goes to DashScope, and this Terraform provisions the ECS, VPC, and EIP on Alibaba Cloud. One command from nothing to this running box." |

---

## Tips

- Keep it tight — this clip is *evidence*, not storytelling. No need to demo features here.
- The three strongest proofs, in order: **ECS metadata region/instance-id from inside the box**,
  **`docker compose ps` showing the stack**, and **`/health` → Qwen Cloud + `llm_ok: true`**.
- If you'd rather not show SSH, Shots 1–2 (console) + Shot 4 (`/health` from the public IP) are
  already sufficient proof.
- Redact nothing sensitive appears on screen — the SSH key file name is fine; never show the
  key contents or `.secrets.env`.
