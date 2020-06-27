resource "aws_s3_bucket" "raw_games" {
  bucket = "velkoz-raw-games"
  acl    = "private"
}