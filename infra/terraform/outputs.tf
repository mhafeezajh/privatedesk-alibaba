output "public_ip" {
  description = "Elastic IP bound to the ECS instance."
  value       = alicloud_eip_address.this.ip_address
}

output "app_url" {
  description = "The Next.js cockpit."
  value       = "http://${alicloud_eip_address.this.ip_address}:3000"
}

output "health_url" {
  description = "API health probe (expect llm_ok: true)."
  value       = "http://${alicloud_eip_address.this.ip_address}:8000/health"
}

output "ssh_command" {
  description = "SSH into the box."
  value       = "ssh -i ${abspath(local_sensitive_file.private_key.filename)} root@${alicloud_eip_address.this.ip_address}"
}

output "isolation_test_command" {
  description = "Prove the ethical wall on the running box."
  value       = "ssh -i ${abspath(local_sensitive_file.private_key.filename)} root@${alicloud_eip_address.this.ip_address} 'cd privatedesk-memoryagent && docker compose exec -T api pytest -q tests/test_isolation.py'"
}

output "private_key_path" {
  description = "Local path to the generated SSH private key (git-ignored)."
  value       = abspath(local_sensitive_file.private_key.filename)
}
