provider "aws" {
    region = "us-east-1"
    version = "~> 2.40"
}
variable "application_name" {
    default = "velkoz-tentacle-gamelist"
}

variable "region" {
    default = "us-east-1"
}

variable "aws_account_id" {
    default = "249914645072"
}
