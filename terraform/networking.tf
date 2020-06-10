resource "aws_vpc" "main" { 
    cidr_block = "172.30.0.0/16"
}

resource "aws_security_group" "open" {
  name        = "velkoz_open"
  description = "Open internet access"
  vpc_id      = aws_vpc.main.id

  ingress {
      from_port = 0
      to_port = 0
      protocol = "-1"
      cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
      from_port = 0
      to_port = 0
      protocol = "-1"
      cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_subnet" "open_subnet" { 
  vpc_id = aws_vpc.main.id
  cidr_block = "172.30.0.0/16"
}

resource "aws_route_table" "velkoz" { 
  vpc_id = aws_vpc.main.id

  route {
      cidr_block = mongodbatlas_network_container.velkoz.atlas_cidr_block
      vpc_peering_connection_id = mongodbatlas_network_peering.velkoz.connection_id
  }
}