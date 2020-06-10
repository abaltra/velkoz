resource "aws_sns_topic" "gamelist_update_requested" {
  name = "gamelist-update-requested"
}

resource "aws_sns_topic_subscription" "update_roll_lambda" {
  topic_arn = aws_sns_topic.gamelist_update_requested.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.update_roll_handler.arn
}