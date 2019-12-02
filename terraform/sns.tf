resource "aws_sns_topic" "player_update_required" {
  name = "player-update-required"

    policy = <<EOF
{
  "Version": "2008-10-17",
  "Id": "__default_policy_ID",
  "Statement": [
    {
      "Sid": "__default_statement_ID",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": [
        "SNS:Publish",
        "SNS:RemovePermission",
        "SNS:SetTopicAttributes",
        "SNS:DeleteTopic",
        "SNS:ListSubscriptionsByTopic",
        "SNS:GetTopicAttributes",
        "SNS:Receive",
        "SNS:AddPermission",
        "SNS:Subscribe"
      ],
      "Resource": "arn:aws:sns:${var.region}:${var.aws_account_id}:player-update-required",
      "Condition": {
        "StringEquals": {
          "AWS:SourceOwner": "${var.aws_account_id}"
        }
      }
    }
  ]
}
EOF
}
