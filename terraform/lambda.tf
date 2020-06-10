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
    vpc_config {
      security_group_ids = [aws_security_group.open.id]
      subnet_ids = [aws_subnet.open_subnet.id]
    }
    environment {
      variables = {
        RIOT_API_KEY = "TBD"
      }
    }
    
}

resource "aws_cloudwatch_log_group" "valkoz_logs" {
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
      "Sid": "AllowManagementOfNetworkResources",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": [ "*" ]
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

resource "aws_lambda_permission" "withSns" {
  statement_id = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_roll_handler.arn
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.gamelist_update_requested.arn
}