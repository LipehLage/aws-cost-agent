# Deploy opcional: Lambda agendada que roda o agente e publica o relatório
# em um tópico SNS. Empacote o código antes com scripts/package.sh (gera
# build/lambda.zip) ou ajuste o caminho em var.lambda_zip.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_sns_topic" "cost_reports" {
  name = "aws-cost-agent-reports"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.report_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.cost_reports.arn
  protocol  = "email"
  endpoint  = var.report_email
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "aws-cost-agent-lambda"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "permissions" {
  statement {
    sid       = "CostExplorer"
    actions   = ["ce:GetCostAndUsage"]
    resources = ["*"]
  }
  statement {
    sid       = "PublishReport"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.cost_reports.arn]
  }
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "aws-cost-agent-permissions"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.permissions.json
}

resource "aws_lambda_function" "agent" {
  function_name = "aws-cost-agent"
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.12"
  handler       = "lambda_handler.handler"
  filename      = var.lambda_zip
  timeout       = 120
  memory_size   = 256

  environment {
    variables = {
      GEMINI_API_KEY = var.gemini_api_key
      SNS_TOPIC_ARN  = aws_sns_topic.cost_reports.arn
      ANALYSIS_DAYS  = tostring(var.analysis_days)
    }
  }
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "aws-cost-agent-schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule = aws_cloudwatch_event_rule.schedule.name
  arn  = aws_lambda_function.agent.arn
}

resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
