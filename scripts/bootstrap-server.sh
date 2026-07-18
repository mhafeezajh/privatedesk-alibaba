#!/usr/bin/env bash
# Runs ON the Ubuntu ECS server. Installs Docker + tooling if missing. Idempotent.
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y curl unzip ca-certificates
  curl -fsSL https://get.docker.com | sh
fi

# Swap safety net: the Next.js production build spikes memory and can OOM on small boxes.
# A swapfile lets the build complete on low-RAM instances. Idempotent.
if ! swapon --show 2>/dev/null | grep -q '/swapfile'; then
  fallocate -l 4G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=4096
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

docker --version
docker compose version
echo "server ready"
