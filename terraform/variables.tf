variable "aws_region" {
  description = "Região onde a Lambda roda (Cost Explorer é global)"
  type        = string
  default     = "us-east-1"
}

variable "gemini_api_key" {
  description = "Chave da Gemini API (vazio = relatório básico sem LLM)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "report_email" {
  description = "E-mail que recebe o relatório via SNS (vazio = sem subscription)"
  type        = string
  default     = ""
}

variable "analysis_days" {
  description = "Janela de análise em dias"
  type        = number
  default     = 30
}

variable "schedule_expression" {
  description = "Agenda da execução (padrão: toda segunda 09:00 UTC)"
  type        = string
  default     = "cron(0 9 ? * MON *)"
}

variable "lambda_zip" {
  description = "Caminho do pacote da Lambda"
  type        = string
  default     = "../build/lambda.zip"
}
