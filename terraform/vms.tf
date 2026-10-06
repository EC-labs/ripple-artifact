data "aws_ami" "nixos" {
  most_recent = true

  filter {
    name   = "name"
    values = ["nixos/25.11.12484.b6018f87da91-x86_64-linux"]
  }

  owners = ["427812963091"]
}

resource "aws_key_pair" "ripple" {
  key_name   = "ripple-key"
  public_key = file("${path.module}/../nixos/secrets/id_ed25519.pub")
}

resource "aws_instance" "ripple_master" {
  ami           = data.aws_ami.nixos.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.ripple_subnet.id

  key_name = aws_key_pair.ripple.key_name

  vpc_security_group_ids = [aws_security_group.ripple_sg.id]

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = {
    Name = "ripple-master"
  }

  lifecycle {
    # New Canonical AMI releases must not replace the running fleet.
    ignore_changes = [ami]
  }
}


resource "aws_instance" "ripple_worker1" {
  ami           = data.aws_ami.nixos.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.ripple_subnet.id

  key_name = aws_key_pair.ripple.key_name

  vpc_security_group_ids = [aws_security_group.ripple_sg.id]

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = {
    Name = "ripple-worker1"
  }

  lifecycle {
    # New Canonical AMI releases must not replace the running fleet.
    ignore_changes = [ami]
  }
}

resource "aws_instance" "ripple_worker2" {
  ami           = data.aws_ami.nixos.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.ripple_subnet.id

  key_name = aws_key_pair.ripple.key_name

  vpc_security_group_ids = [aws_security_group.ripple_sg.id]

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = {
    Name = "ripple-worker2"
  }

  lifecycle {
    # New Canonical AMI releases must not replace the running fleet.
    ignore_changes = [ami]
  }
}

resource "aws_eip" "master" {
  instance = aws_instance.ripple_master.id
  domain   = "vpc"

  tags = {
    Name = "master-eip"
  }
}

resource "aws_eip" "worker1" {
  instance = aws_instance.ripple_worker1.id
  domain   = "vpc"

  tags = {
    Name = "worker1-eip"
  }
}

resource "aws_eip" "worker2" {
  instance = aws_instance.ripple_worker2.id
  domain   = "vpc"

  tags = {
    Name = "worker2-eip"
  }
}
