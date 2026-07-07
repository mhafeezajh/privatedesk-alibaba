#!/usr/bin/env bash
# Runs ON the Ubuntu ECS server. Installs Docker + tooling if missing. Idempotent.
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y curl unzip ca-certificates
  curl -fsSL https://get.docker.com | sh
fi

docker --version
docker compose version
echo "server ready"
