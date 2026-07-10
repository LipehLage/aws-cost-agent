output "lambda_function_name" {
  value = aws_lambda_function.agent.function_name
}

output "sns_topic_arn" {
  value = aws_sns_topic.cost_reports.arn
}
