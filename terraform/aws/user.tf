resource "aws_iam_user" "stitch_user" {
    name = "stitch-publisher"
}

resource "aws_iam_access_key" "stitch_access_key" {
  user = aws_iam_user.stitch_user.name
}

resource "aws_iam_user_policy" "stitch_policy" {
    name = "stitch-publisher-policy"
    user = aws_iam_user.stitch_user.name
    
    policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "sns:Publish"
            ],
            "Effect": "Allow",
            "Resource": "${aws_sns_topic.player_update_required.arn}"
        }
    ]
}
EOF
}


