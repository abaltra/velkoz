terraform {
    backend "s3" {
        bucket = "abaltra-tfstates"
        key = "velkoz-tentacles-lol-gamelist"
        region = "us-east-1"
    }
}