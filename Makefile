# PrivateDesk MemoryAgent — task runner
# Local:  make dev
# Remote: make deploy IP=1.2.3.4 KEY=~/privatedesk.pem [USER=root]

IP  ?=
KEY ?=
USER ?= root

TF_DIR ?= infra/terraform

API_BASE ?= http://localhost:8000

.PHONY: help dev logs health seed test smoke evals down deploy infra-plan infra-up infra-down infra-output infra-stop infra-start

help:
	@echo "make dev                                   build + run locally, wait for health, seed"
	@echo "make logs                                  follow API logs"
	@echo "make health                                print /health (JSON)"
	@echo "make seed                                  seed the legal demo"
	@echo "make test                                  run the isolation guard test"
	@echo "make smoke [API_BASE=http://host:8000]     API smoke test (auth + both walls)"
	@echo "make evals [API_BASE=http://host:8000]     score the four behaviors (100/100)"
	@echo "make down                                  stop the stack"
	@echo "make deploy IP=1.2.3.4 KEY=key.pem [USER=root]   deploy to an existing Ubuntu ECS box"
	@echo "make infra-up                              provision Alibaba Cloud + deploy via Terraform (whole package)"
	@echo "make infra-plan                            preview the Terraform plan"
	@echo "make infra-output                          show app URL / health / ssh from Terraform state"
	@echo "make infra-stop                            stop the ECS instance (halt compute billing; keep disk+EIP)"
	@echo "make infra-start                           start the ECS instance again (same EIP; app auto-restarts)"
	@echo "make infra-down                            destroy all Terraform-managed cloud resources"

dev:
	bash scripts/dev-up.sh

logs:
	docker compose logs -f api

health:
	curl -fsS http://localhost:8000/health | python3 -m json.tool

seed:
	curl -fsS -X POST http://localhost:8000/api/demo/seed -H 'content-type: application/json' -d '{"scenario":"legal"}' | python3 -m json.tool

test:
	docker compose exec api pytest -q tests/test_isolation.py

smoke:
	API=$(API_BASE) bash scripts/smoke-test.sh

evals:
	EVAL_API_BASE=$(API_BASE) python3 evals/run_evals.py

down:
	docker compose down

deploy:
	@test -n "$(IP)"  || { echo "set IP=…  (the ECS public IP)"; exit 1; }
	@test -n "$(KEY)" || { echo "set KEY=… (path to your .pem)"; exit 1; }
	bash scripts/deploy-remote.sh $(IP) $(KEY) $(USER)

# ---- Infrastructure-as-Code (Alibaba Cloud, full package) --------------------
# Needs: ALICLOUD_ACCESS_KEY, ALICLOUD_SECRET_KEY, TF_VAR_dashscope_api_key in env.
infra-plan:
	cd $(TF_DIR) && terraform init -input=false && terraform plan

infra-up:
	cd $(TF_DIR) && terraform init -input=false && terraform apply
	@$(MAKE) infra-output

infra-output:
	@cd $(TF_DIR) && terraform output

infra-stop:
	cd $(TF_DIR) && terraform apply -auto-approve -var instance_status=Stopped
	@echo "Instance stopped (StopCharging). Compute billing halted; disk + EIP remain. Restart: make infra-start"

infra-start:
	cd $(TF_DIR) && terraform apply -auto-approve -var instance_status=Running
	@$(MAKE) infra-output

infra-down:
	cd $(TF_DIR) && terraform destroy
