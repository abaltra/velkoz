resource "aws_lambda_event_source_mapping" "dynamo_update_roll_event" { 
  event_source_arn = aws_dynamodb_table.lol_player_update_roll.stream_arn
  starting_position = "LATEST"
  function_name = aws_lambda_function.update_roll_handler.function_name

  depends_on = [aws_iam_role_policy.iam_policy_lambda]
}

resource "aws_lambda_function" "update_roll_handler" {
    function_name = "lol-update-roll-handler"
    filename = "lol-update-roll.zip"
    handler = "main.handler"
    source_code_hash = filebase64sha256("lol-update-roll.zip")
    runtime = "nodejs12.x"
    role = aws_iam_role.iam_for_lambda.arn
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
        "Resource": "${aws_dynamodb_table.lol_player_update_roll.arn}/*"
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
    }
  ]
}
EOF
}

# resource "aws_iam_role_policy_attachment" "iam_policy_attachment_lambda" { 
#   policy_arn = aws_iam_role_policy.iam_policy_lambda.arn
#   role = aws_iam_role.iam_for_lambda.name
# }

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