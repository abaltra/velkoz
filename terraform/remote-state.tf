terraform {
    backend "s3" {
        bucket = "abaltra-tfstates"
        key = "velkoz-core"
        region = "us-east-1"
    }
}