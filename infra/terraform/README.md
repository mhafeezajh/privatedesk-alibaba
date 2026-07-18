# Infrastructure-as-Code — PrivateDesk MemoryAgent (Alibaba Cloud)

One `terraform apply` goes from nothing to a live, seeded demo. Terraform stands up
the network and VM, then ships the source, renders the server-side `.env`, builds the
web app with the correct `NEXT_PUBLIC_API_BASE`, brings the Docker Compose stack up,
waits for health, and seeds the legal demo.

```
VPC ─ vSwitch ─ Security Group ─ ECS (Ubuntu 24.04) ─ EIP
                     │                    │
        only 22/8000/3000 open      Docker Compose:
        (5432/6333/6379 closed)     postgres · qdrant · redis · api · web
```

## What it creates
| Resource | Purpose |
|---|---|
| `alicloud_vpc` + `alicloud_vswitch` | Isolated network in one zone |
| `alicloud_security_group` (+ rules) | **Only** 22 (admin), 3000, 8000 inbound; all egress |
| `alicloud_ecs_key_pair` + generated RSA key | SSH access (private key written to `generated/`, git-ignored) |
| `alicloud_instance` | Ubuntu 24.04 box — default `ecs.u1-c1m4.large` (2 vCPU / 8 GB) |
| `alicloud_eip_address` + association | Stable public IP |
| `null_resource.deploy` | Ships source, renders `.env`, `docker compose up`, seeds |

> **Wall preserved (CLAUDE.md #5):** the security group never opens Postgres/Qdrant/Redis.
> They remain on the internal Docker network behind the SG.

## Prerequisites
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
- An Alibaba Cloud AccessKey pair with ECS/VPC/EIP permissions
- A DashScope API key (Model Studio → enable Free Quota) for the cloud LLM path
- `tar`, `ssh`, `curl` locally (the packaging + provisioners use them)

## Usage
```bash
cd infra/terraform

# 1. Credentials (never committed)
export ALICLOUD_ACCESS_KEY="LTAI..."
export ALICLOUD_SECRET_KEY="..."
export TF_VAR_dashscope_api_key="sk-..."

# 2. Optional: copy and tweak variables (region, instance size, admin_cidr…)
cp terraform.tfvars.example terraform.tfvars

# 3. Go
terraform init
terraform apply

# 4. Outputs
terraform output app_url          # http://<eip>:3000
terraform output health_url       # expect "llm_ok": true
terraform output ssh_command
```

From the repo root you can also use `make infra-up` / `make infra-plan` / `make infra-down`.

## Redeploying app code
Edit the app, then re-apply — the deploy step re-runs when the box or rendered `.env`
changes. To force a rebuild after a pure code change:
```bash
terraform apply -replace=null_resource.deploy
```
(Or use the existing `make deploy IP=<eip> KEY=$(terraform output -raw private_key_path)`.)

## Prove the wall
```bash
eval "$(terraform output -raw isolation_test_command)"
# runs tests/test_isolation.py on the box — zero cross-namespace leakage
```

## Teardown
```bash
terraform destroy
```
Deletes everything, including the EIP (billing stops). The generated SSH key under
`generated/` is left on your disk; remove it manually if you want.

## Notes / gotchas
- **`admin_cidr`** defaults to `0.0.0.0/0` so the provisioner connects from wherever you
  run Terraform. Set it to `your.ip/32` for anything longer-lived. The machine running
  `terraform apply` must be inside this range or the remote provisioner will hang.
- **State holds secrets** (the rendered `.env`, the private key). Keep `*.tfstate` out of
  git (the local `.gitignore` does this) and use a remote encrypted backend for real use.
- **Instance type availability** varies by region/zone; if `apply` fails on capacity, set a
  different `instance_type` or `region`.
- This is a single-box demo topology, matching the project's "one matter = one namespace"
  lean build. Multi-node / managed Postgres / TLS termination are extensions on top.
