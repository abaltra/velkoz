resource "aws_lambda_function" "lol_gamelist" {
  filename = "lol-gamelist-lambda.zip"
  function_name = "lol-gamelist"
  role = aws_iam_role.lol_gamelist_worker_role.arn
  handler = "index.handler"

  source_code_hash = filebase64sha256("lol-gamelist-lambda.zip")

  runtime = "nodejs12.x"

  environment {
      variables = {
          RIOT_API_KEY = var.lol_api_key
          MONGO_CONNECTION_STRING = var.mongo_connection_string
          NEW_GAME_FOUND_TOPIC_ARN = aws_sns_topic.new_game_found.arn
      }
  }
}

resource "aws_lambda_permission" "lol_gamelist_sns_permission" {
  statement_id = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lol_gamelist.function_name
  principal = "sns.amazonaws.com"
  source_arn = "arn:aws:sns:${var.region}:${var.aws_account_id}:player-update-required"
}


resource "aws_sns_topic_subscription" "lol_gamelist_sns_subscription" {
  topic_arn = "arn:aws:sns:${var.region}:${var.aws_account_id}:player-update-required"
  protocol = "lambda"
  endpoint = aws_lambda_function.lol_gamelist.arn
}

