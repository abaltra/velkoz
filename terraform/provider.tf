provider "aws" {
  region  = "us-east-1"
  profile = "abaltra"
}

# provider "mongodbatlas" {
#     version = "~> 0.3"
# }

variable "application_name" {
    default = "velkoz-core"
}

variable "region" {
    default = "us-east-1"
}

variable "aws_account_id" {
    default = "249914645072"
}