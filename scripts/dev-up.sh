#!/usr/bin/env bash
# Local bring-up: build the stack, start it, wait for health, optionally seed.
set -euo pipefail
cd "$(dirname "$0")/.."

info(){ printf "\033[36m▶ %s\033[0m\n" "$*"; }
ok(){   printf "\033[32m✓ %s\033[0m\n" "$*"; }
warn(){ printf "\033[33m! %s\033[0m\n" "$*"; }
die(){  printf "\033[31m✗ %s\033[0m\n" "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "Docker not found. Install Docker Desktop first."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 not found (need 'docker compose')."

if [ ! -f .env ]; then
  cp .env.example .env
  warn "Created .env from the template."
  warn "Edit it and set DASHSCOPE_API_KEY (or leave it empty to run fully local on Ollama), then re-run."
  exit 0
fi

if ! grep -q '^DASHSCOPE_API_KEY=..*' .env; then
  warn "DASHSCOPE_API_KEY is empty in .env — the app will use the local Ollama fallback if configured."
fi

info "Building and starting the stack (first run pulls images + builds the web app)…"
docker compose up --build -d

info "Waiting for the API to become healthy…"
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8000/health >/tmp/pd_health 2>/dev/null; then
    ok "API is up."
    cat /tmp/pd_health; echo
    break
  fi
  if [ "$i" = 60 ]; then die "API didn't become healthy in time. Inspect: docker compose logs api"; fi
  sleep 3
done

read -r -p "Seed the legal demo now (3 matters + discovery)? [Y/n] " ans || ans="Y"
case "${ans:-Y}" in
  n|N) : ;;
  *) curl -fsS -X POST http://localhost:8000/api/demo/seed \
        -H 'content-type: application/json' -d '{"scenario":"legal"}' >/dev/null \
        && ok "Seeded the firm and three matters." ;;
esac

ok "App:    http://localhost:3000"
ok "Health: http://localhost:8000/health"
echo "   Logs:   docker compose logs -f api    ·    Stop: docker compose down"
