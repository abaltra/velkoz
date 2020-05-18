terraform {
    backend "s3" {
        bucket = "abaltra-tfstates"
        key = "velkoz-core/terraform.tfstate"
        region = "us-east-1"
        profile = "abaltra"
    }
}