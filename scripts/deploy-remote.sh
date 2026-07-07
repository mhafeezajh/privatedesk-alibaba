#!/usr/bin/env bash
# Deploy to an existing Ubuntu ECS instance over SSH.
#   bash scripts/deploy-remote.sh <PUBLIC_IP> <SSH_KEY> [SSH_USER]
# Assumes: the instance exists, is reachable by SSH, and its security group
# already allows inbound TCP 22 (you), 8000, and 3000.
set -euo pipefail
cd "$(dirname "$0")/.."

IP="${1:-}"; KEY="${2:-}"; SSH_USER="${3:-root}"
REMOTE_DIR="privatedesk-memoryagent"

info(){ printf "\033[36m▶ %s\033[0m\n" "$*"; }
ok(){   printf "\033[32m✓ %s\033[0m\n" "$*"; }
die(){  printf "\033[31m✗ %s\033[0m\n" "$*" >&2; exit 1; }

[ -n "$IP" ] && [ -n "$KEY" ] || die "usage: deploy-remote.sh <PUBLIC_IP> <SSH_KEY> [SSH_USER]"
[ -f "$KEY" ] || die "SSH key not found: $KEY"
[ -f .env ]  || die "Local .env not found. Create it (with DASHSCOPE_API_KEY) before deploying."
grep -q '^DASHSCOPE_API_KEY=..*' .env || printf "\033[33m! DASHSCOPE_API_KEY looks empty in .env\033[0m\n"

SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$SSH_USER@$IP")
SCP=(scp -i "$KEY" -o StrictHostKeyChecking=accept-new)

info "Packaging source (excluding heavy/dev dirs)…"
tar czf /tmp/pd_deploy.tgz \
  --exclude='node_modules' --exclude='.next' --exclude='.git' \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='venv' \
  api web docker-compose.yml litellm_config.yaml .env.example LICENSE README.md scripts

info "Shipping to $SSH_USER@$IP:$REMOTE_DIR …"
"${SSH[@]}" "mkdir -p $REMOTE_DIR"
"${SCP[@]}" /tmp/pd_deploy.tgz "$SSH_USER@$IP:$REMOTE_DIR/"
"${SCP[@]}" .env "$SSH_USER@$IP:$REMOTE_DIR/.env"

info "Bootstrapping server (installs Docker if missing)…"
"${SSH[@]}" "cd $REMOTE_DIR && tar xzf pd_deploy.tgz && rm -f pd_deploy.tgz && bash scripts/bootstrap-server.sh"

info "Building + starting (API base baked as http://$IP:8000)…"
"${SSH[@]}" "cd $REMOTE_DIR && NEXT_PUBLIC_API_BASE=http://$IP:8000 docker compose up --build -d"

info "Waiting for health…"
"${SSH[@]}" "for i in \$(seq 1 80); do curl -fsS http://localhost:8000/health && exit 0; sleep 3; done; exit 1" \
  || die "API didn't become healthy. Inspect: ssh -i $KEY $SSH_USER@$IP 'cd $REMOTE_DIR && docker compose logs api'"
echo

info "Seeding the legal demo…"
"${SSH[@]}" "curl -fsS -X POST http://localhost:8000/api/demo/seed -H 'content-type: application/json' -d '{\"scenario\":\"legal\"}' >/dev/null && echo seeded"

echo
ok "Deployed."
echo "   App:    http://$IP:3000"
echo "   Health: http://$IP:8000/health"
echo "   If those don't load, open inbound TCP 3000 and 8000 in the ECS security group."
