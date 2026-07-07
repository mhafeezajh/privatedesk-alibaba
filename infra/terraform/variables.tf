variable "region" {
  description = "Alibaba Cloud region. Singapore keeps the box near the DashScope intl endpoint."
  type        = string
  default     = "ap-southeast-1"
}

variable "project" {
  description = "Name prefix for all created resources."
  type        = string
  default     = "privatedesk"
}

variable "dashscope_api_key" {
  description = <<-EOT
    DASHSCOPE_API_KEY for the Qwen Cloud path. Rendered into the server-side .env.
    Leave empty ONLY if the server will reach a local Ollama itself (not the usual cloud demo).
    Set via `export TF_VAR_dashscope_api_key=sk-...` — never hardcode it in a committed .tfvars.
  EOT
  type        = string
  default     = ""
  sensitive   = true
}

variable "instance_type" {
  description = "ECS instance type. Default ~4 vCPU / 16 GB, enough for the full compose stack."
  type        = string
  # ecs.u1-c1m4.xlarge = economical universal x86, 4 vCPU / 16 GB; available in
  # ap-southeast-1 (the g6 family is not offered there). Override per region as needed.
  default = "ecs.u1-c1m4.xlarge"
}

variable "system_disk_size" {
  description = "Root disk size in GB (images + build cache need headroom)."
  type        = number
  default     = 40
}

variable "eip_bandwidth" {
  description = "EIP outbound bandwidth cap in Mbit/s."
  type        = number
  default     = 10
}

variable "admin_cidr" {
  description = <<-EOT
    CIDR allowed to reach SSH (port 22). Lock this to your own IP, e.g. "203.0.113.4/32".
    The default is wide open and is fine only for a short-lived hackathon box —
    the same machine running `terraform apply` must be inside this range for the
    remote provisioner to connect.
  EOT
  type        = string
  default     = "0.0.0.0/0"
}

variable "app_cidr" {
  description = "CIDR allowed to reach the app (web 3000) and API (8000). Public by default for demoing."
  type        = string
  default     = "0.0.0.0/0"
}

variable "vpc_cidr" {
  description = "VPC address space."
  type        = string
  default     = "172.16.0.0/16"
}

variable "vswitch_cidr" {
  description = "vSwitch (subnet) address space, inside the VPC."
  type        = string
  default     = "172.16.1.0/24"
}

variable "k_candidates" {
  description = <<-EOT
    Vector-search candidate pool size the reranker considers (K_CANDIDATES).
    Raised from the app default of 20 so high-salience facts on large matters
    (100+ memories) reliably enter the rerank pool. K_CONTEXT (top-k into the
    prompt) stays bounded separately.
  EOT
  type        = number
  default     = 64
}

variable "seed_demo" {
  description = "POST the legal demo seed after the stack is healthy."
  type        = bool
  default     = true
}

variable "session_secret" {
  description = "App SESSION_SECRET. Leave empty to auto-generate a random one."
  type        = string
  default     = ""
  sensitive   = true
}
