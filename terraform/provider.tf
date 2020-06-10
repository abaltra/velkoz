provider "aws" {
  region  = "us-east-1"
  profile = "abaltra"
}

provider "mongodbatlas" {
    version = "~> 0.4"
}

variable "application_name" {
    default = "velkoz-core"
}

variable "region" {
    default = "us-east-1"
}