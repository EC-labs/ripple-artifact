resource "aws_vpc" "ripple_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "ripple-vpc"
  }
}

resource "aws_subnet" "ripple_subnet" {
  vpc_id            = aws_vpc.ripple_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.region}a"

  tags = {
    Name = "ripple-subnet"
  }
}

resource "aws_internet_gateway" "ripple_igw" {
  vpc_id = aws_vpc.ripple_vpc.id

  tags = {
    Name = "ripple-igw"
  }
}

resource "aws_route_table" "ripple_rt" {
  vpc_id = aws_vpc.ripple_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ripple_igw.id
  }

  tags = {
    Name = "ripple-rt"
  }
}

resource "aws_route_table_association" "ripple_rta" {
  subnet_id      = aws_subnet.ripple_subnet.id
  route_table_id = aws_route_table.ripple_rt.id
}

resource "aws_security_group" "ripple_sg" {
  name        = "ripple-sg"
  description = "Ripple security group"
  vpc_id      = aws_vpc.ripple_vpc.id
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "kube_api_server" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "tcp"
  from_port         = 6443
  to_port           = 6443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "internal_allow_all" {
  security_group_id            = aws_security_group.ripple_sg.id
  ip_protocol                  = "-1"
  from_port                    = -1
  to_port                      = -1
  referenced_security_group_id = aws_security_group.ripple_sg.id
}


resource "aws_vpc_security_group_ingress_rule" "allow_public_master" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "-1"
  from_port         = -1 
  to_port           = -1
  cidr_ipv4         = "${aws_eip.master.public_ip}/32"
}

resource "aws_vpc_security_group_ingress_rule" "allow_public_worker1" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "-1"
  from_port         = -1 
  to_port           = -1
  cidr_ipv4         = "${aws_eip.worker1.public_ip}/32"
}

resource "aws_vpc_security_group_ingress_rule" "allow_public_worker2" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "-1"
  from_port         = -1
  to_port           = -1
  cidr_ipv4         = "${aws_eip.worker2.public_ip}/32"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.ripple_sg.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
