# ---------------------------------------------------------------------------
# Network: one VPC, one vSwitch, one security group.
#
# INVARIANT (CLAUDE.md #5): only 22 / 8000 / 3000 are ever reachable from
# outside. Postgres (5432), Qdrant (6333) and Redis (6379) are NEVER opened —
# they stay on the Docker network behind this security group, which is the
# externally-enforced wall even though compose publishes them on the host.
# ---------------------------------------------------------------------------

data "alicloud_zones" "default" {
  available_instance_type = var.instance_type
  available_disk_category = "cloud_essd"
}

resource "alicloud_vpc" "this" {
  vpc_name   = "${var.project}-vpc"
  cidr_block = var.vpc_cidr
}

resource "alicloud_vswitch" "this" {
  vswitch_name = "${var.project}-vswitch"
  vpc_id       = alicloud_vpc.this.id
  cidr_block   = var.vswitch_cidr
  zone_id      = data.alicloud_zones.default.zones[0].id
}

resource "alicloud_security_group" "this" {
  security_group_name = "${var.project}-sg"
  description         = "PrivateDesk: SSH (admin), web 3000, api 8000. Data ports stay closed."
  vpc_id              = alicloud_vpc.this.id
}

# --- Ingress: exactly three ports, nothing else -----------------------------
resource "alicloud_security_group_rule" "ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.this.id
  cidr_ip           = var.admin_cidr
  description       = "SSH — admin only"
}

resource "alicloud_security_group_rule" "web" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "3000/3000"
  priority          = 1
  security_group_id = alicloud_security_group.this.id
  cidr_ip           = var.app_cidr
  description       = "Next.js cockpit"
}

resource "alicloud_security_group_rule" "api" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "8000/8000"
  priority          = 1
  security_group_id = alicloud_security_group.this.id
  cidr_ip           = var.app_cidr
  description       = "FastAPI"
}

# --- Egress: allow all outbound (DashScope, image pulls, apt) ----------------
resource "alicloud_security_group_rule" "egress_all" {
  type              = "egress"
  ip_protocol       = "all"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "-1/-1"
  priority          = 1
  security_group_id = alicloud_security_group.this.id
  cidr_ip           = "0.0.0.0/0"
  description       = "All outbound"
}
