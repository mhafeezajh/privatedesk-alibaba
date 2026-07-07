# ---------------------------------------------------------------------------
# App deploy: package the repo, ship it, render .env, build with the correct
# NEXT_PUBLIC_API_BASE, bring the stack up, wait for health, seed the demo.
#
# This mirrors scripts/deploy-remote.sh, but driven entirely by Terraform so a
# single `terraform apply` goes from nothing to a live URL.
# ---------------------------------------------------------------------------

locals {
  repo_root      = abspath("${path.module}/../..")
  build_dir      = "${path.module}/build"
  source_tarball = "${path.module}/build/source.tgz"
  remote_dir     = "/root/privatedesk-memoryagent"

  session_secret = coalesce(var.session_secret, random_password.session.result)

  env_file = templatefile("${path.module}/templates/env.tftpl", {
    dashscope_api_key = var.dashscope_api_key
    session_secret    = local.session_secret
    k_candidates      = var.k_candidates
  })

  # Content hash of everything we ship, so an app code change re-runs the deploy
  # on `terraform apply` (scoped to source dirs — never node_modules/.next).
  source_files = sort(tolist(setunion(
    fileset(local.repo_root, "api/**/*.py"),
    fileset(local.repo_root, "api/requirements.txt"),
    fileset(local.repo_root, "api/Dockerfile"),
    fileset(local.repo_root, "web/app/**"),
    fileset(local.repo_root, "web/components/**"),
    fileset(local.repo_root, "web/lib/**"),
    fileset(local.repo_root, "web/package.json"),
    fileset(local.repo_root, "web/package-lock.json"),
    fileset(local.repo_root, "web/Dockerfile"),
    fileset(local.repo_root, "web/next.config.mjs"),
    fileset(local.repo_root, "web/tailwind.config.ts"),
    fileset(local.repo_root, "web/postcss.config.mjs"),
    fileset(local.repo_root, "web/tsconfig.json"),
    fileset(local.repo_root, "docker-compose.yml"),
    fileset(local.repo_root, "litellm_config.yaml"),
  )))
  source_hash = sha256(join(",", [for f in local.source_files : filesha256("${local.repo_root}/${f}")]))
}

resource "random_password" "session" {
  length  = 48
  special = false
}

resource "null_resource" "deploy" {
  # Re-run the app deploy whenever the box changes or the rendered env changes.
  triggers = {
    instance    = alicloud_instance.this.id
    eip         = alicloud_eip_address.this.ip_address
    env_hash    = sha256(local.env_file)
    source_hash = local.source_hash
  }

  depends_on = [
    alicloud_eip_association.this,
    alicloud_security_group_rule.ssh,
  ]

  connection {
    type        = "ssh"
    host        = alicloud_eip_address.this.ip_address
    user        = "root"
    private_key = tls_private_key.ssh.private_key_pem
    timeout     = "5m"
  }

  # 1. Package the source locally (tar handles the exclude globs cleanly).
  provisioner "local-exec" {
    working_dir = local.repo_root
    command     = <<-EOT
      mkdir -p "${abspath(local.build_dir)}"
      tar czf "${abspath(local.source_tarball)}" \
        --exclude='node_modules' --exclude='.next' --exclude='.git' \
        --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' \
        --exclude='venv' --exclude='infra/terraform/.terraform' \
        --exclude='infra/terraform/build' --exclude='infra/terraform/generated' \
        api web docker-compose.yml litellm_config.yaml .env.example LICENSE README.md scripts
    EOT
  }

  # 2. Ensure the target dir exists (also serves as the SSH-ready gate).
  provisioner "remote-exec" {
    inline = ["mkdir -p ${local.remote_dir}"]
  }

  # 3. Upload the source and the rendered .env.
  provisioner "file" {
    source      = local.source_tarball
    destination = "${local.remote_dir}/source.tgz"
  }

  provisioner "file" {
    content     = local.env_file
    destination = "${local.remote_dir}/.env"
  }

  # 4. Unpack, install Docker if missing, build + start, wait for health, seed.
  provisioner "remote-exec" {
    inline = [
      "set -e",
      "cd ${local.remote_dir}",
      "tar xzf source.tgz && rm -f source.tgz",
      "bash scripts/bootstrap-server.sh",
      "NEXT_PUBLIC_API_BASE=http://${alicloud_eip_address.this.ip_address}:8000 docker compose up --build -d",
      "echo 'Waiting for API health…'",
      "for i in $(seq 1 80); do curl -fsS http://localhost:8000/health && break; sleep 3; done",
      var.seed_demo ? "curl -fsS -X POST http://localhost:8000/api/demo/seed -H 'content-type: application/json' -d '{\"scenario\":\"legal\"}' >/dev/null && echo seeded || echo 'seed skipped/failed'" : "echo 'seed disabled'",
    ]
  }
}
