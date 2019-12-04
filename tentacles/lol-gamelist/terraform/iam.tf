resource "aws_iam_role" "lol_gamelist_worker_role" {
  name = "lol-gamelist-worker"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "lol_gamelist_worker_policy" {
  name = "lol-gamelist-worker-policy"
  role = aws_iam_role.lol_gamelist_worker_role.id
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "SNS:Publish"
          ],
          "Resource": "${aws_sns_topic.new_game_found.arn}"
        }
    ]
}
EOF
}

