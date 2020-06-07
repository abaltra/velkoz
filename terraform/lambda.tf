resource "aws_lambda_event_source_mapping" "dynamo_update_roll_event" { 
  event_source_arn = aws_dynamodb_table.player_update_roll.stream_arn
  starting_position = "LATEST"
  function_name = aws_lambda_function.update_roll_handler.function_name

  depends_on = [aws_iam_role_policy.iam_policy_lambda]
}

resource "archive_file" "update_roller_zip" { 
  type = "zip"
  source_dir = "${path.cwd}/../lambdas/update-roller"
  output_path = "./lol-update-roller.zip"

}

resource "aws_lambda_function" "update_roll_handler" {
    function_name = "lol-update-roll-handler"
    filename = "lol-update-roller.zip"
    handler = "index.handler"
    source_code_hash = archive_file.update_roller_zip.output_base64sha256
    runtime = "nodejs12.x"
    role = aws_iam_role.iam_for_lambda.arn
    environment {
      variables = {
        USER_GAMELIST_UPDATE_REQUESTED_TOPIC = aws_sns_topic.player_gamelist_update_requested.arn
      }
    }
    
}

resource "aws_cloudwatch_log_group" "example" {
  name              = "/aws/lambda/${aws_lambda_function.update_roll_handler.function_name}"
  retention_in_days = 14
}

resource "aws_iam_role_policy" "iam_policy_lambda" { 
  name = "policy_for_lambda"
  role = aws_iam_role.iam_for_lambda.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
        "Sid": "AllowDynamoActions",
        "Action": [
            "dynamodb:*"
        ],
        "Effect": "Allow",
        "Resource": "${aws_dynamodb_table.player_update_roll.arn}/*"
    },
    {       
        "Sid": "AllowLambdaFunctionInvocation",
        "Effect": "Allow",
        "Action": [
            "lambda:InvokeFunction"
        ], 
        "Resource": [
            "*"
        ]
    },
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/aws/lambda/${aws_lambda_function.update_roll_handler.function_name}:*",
      "Effect": "Allow"
    },
    {
      "Sid": "AllowSendingSNSMessages",
      "Effect": "Allow",
      "Action": ["sns:Publish"],
      "Resource": [ "${aws_sns_topic.player_gamelist_update_requested.arn}" ]
    }
  ]
}
EOF
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

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