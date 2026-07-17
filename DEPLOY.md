# Deploying PrivateDesk

Two paths. Both assume Docker + Docker Compose v2 locally.

## Run locally
```bash
cp .env.example .env        # then set DASHSCOPE_API_KEY (or leave empty for local Ollama)
make dev                    # builds, starts, waits for health, offers to seed
```
Open http://localhost:3000. Health is at http://localhost:8000/health.

## Deploy to Alibaba Cloud ECS (automated)
You still create the VM yourself (see the click-by-click in `docs/deploy-alibaba-runbook.html`):
an Ubuntu 24.04 instance (2 vCPU / 4 GB is plenty), with a public IP, and a security group allowing
inbound **TCP 22 (your IP), 8000, and 3000**. Then, from your laptop:

```bash
# .env must exist locally with your DASHSCOPE_API_KEY (it is copied to the server, not committed)
make deploy IP=<public-ip> KEY=~/path/to/key.pem            # USER=root by default
```

The script packages the source, ships it over SSH, installs Docker on the server if needed,
builds with `NEXT_PUBLIC_API_BASE=http://<public-ip>:8000` (the #1 gotcha, handled for you),
starts the stack, waits for health, and seeds the legal demo.

When it finishes:
- App:    `http://<public-ip>:3000`
- Health: `http://<public-ip>:8000/health`  → expect `"llm_ok": true`
- Prove the wall: `ssh -i <key> root@<ip> 'cd privatedesk-memoryagent && docker compose exec api pytest -q tests/test_isolation.py'`

## Deploy to Alibaba Cloud (full IaC — Terraform)
If you'd rather not click through the console, `infra/terraform/` stands up the **whole
package** — VPC, vSwitch, security group (only 22/8000/3000 open), key pair, ECS box, and
EIP — then ships the source, renders the server `.env`, builds with the right
`NEXT_PUBLIC_API_BASE`, starts the stack, and seeds the demo. One command from nothing to a
live URL:

```bash
export ALICLOUD_ACCESS_KEY=…  ALICLOUD_SECRET_KEY=…  TF_VAR_dashscope_api_key=sk-…
make infra-up          # terraform apply; prints app_url / health_url / ssh_command
make infra-down        # terraform destroy — tears it all down (billing stops)
```

See [infra/terraform/README.md](infra/terraform/README.md) for variables (region, instance
size, locking `admin_cidr` to your IP) and how to redeploy after code changes. Terraform
state holds secrets — keep `*.tfstate` out of git (the module's `.gitignore` does this).

## Notes
- Keep the instance running until judging closes; add `restart: unless-stopped` to the `api`
  and `web` services if you want them to survive a reboot.
- Re-deploy after code changes: just run `make deploy …` again.
