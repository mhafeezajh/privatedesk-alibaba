# Providers for the PrivateDesk MemoryAgent Alibaba Cloud deployment.
#
# Auth for the alicloud provider is read from the environment (never committed):
#   export ALICLOUD_ACCESS_KEY="…"
#   export ALICLOUD_SECRET_KEY="…"
# The region comes from var.region below.
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.230"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "alicloud" {
  region = var.region
  # access_key / secret_key intentionally omitted — supplied via
  # ALICLOUD_ACCESS_KEY / ALICLOUD_SECRET_KEY environment variables.
}
