resource "aws_s3_bucket" "games" {
  bucket = "lol-games-raw"
  acl = "private"
}
