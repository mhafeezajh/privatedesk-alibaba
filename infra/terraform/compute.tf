# ---------------------------------------------------------------------------
# Compute: SSH key pair, Ubuntu 24.04 ECS instance, and a public EIP.
# ---------------------------------------------------------------------------

# Latest official Ubuntu 24.04 image in this region.
data "alicloud_images" "ubuntu" {
  owners      = "system"
  name_regex  = "^ubuntu_24_04_x64"
  most_recent = true
}

# Generate an SSH key pair. The private key is written locally (0600) so the
# provisioner — and you — can reach the box. It is git-ignored.
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_sensitive_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/generated/${var.project}.pem"
  file_permission = "0600"
}

resource "alicloud_ecs_key_pair" "this" {
  key_pair_name = "${var.project}-key"
  public_key    = tls_private_key.ssh.public_key_openssh
}

resource "alicloud_instance" "this" {
  instance_name   = "${var.project}-api"
  host_name       = "${var.project}-api"
  image_id        = data.alicloud_images.ubuntu.images[0].id
  instance_type   = var.instance_type
  security_groups = [alicloud_security_group.this.id]
  vswitch_id      = alicloud_vswitch.this.id
  key_name        = alicloud_ecs_key_pair.this.key_pair_name

  system_disk_category = "cloud_essd"
  system_disk_size     = var.system_disk_size

  instance_charge_type       = "PostPaid"
  internet_max_bandwidth_out = 0 # public connectivity comes from the EIP below

  tags = {
    project = var.project
    managed = "terraform"
  }
}

resource "alicloud_eip_address" "this" {
  address_name         = "${var.project}-eip"
  bandwidth            = var.eip_bandwidth
  internet_charge_type = "PayByTraffic"
}

resource "alicloud_eip_association" "this" {
  allocation_id = alicloud_eip_address.this.id
  instance_id   = alicloud_instance.this.id
}
