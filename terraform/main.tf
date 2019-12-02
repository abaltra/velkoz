provider "aws" {
    region = "us-east-1"
    version = "~> 2.40"
}

provider "mongodbatlas" {
    version = "~> 0.3"
}

variable "application_name" {
    default = "velkoz-core"
}

variable "region" {
    default = "us-east-1"
}

variable "aws_account_id" {
    default = "249914645072"
}

variable "atlas_org_id" {
    default = "5b4184e4df9db149cda80bd5"
}