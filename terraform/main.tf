provider "aws" {
  region = var.region
}

variable "region" {
  description = "The AWS region"
}

variable "account_id" {
  description = "The AWS account ID"
}

variable "pushover_user_key" {
  description = "The Pushover user key"
}

variable "pushover_api_token" {
  description = "The Pushover API token"
}

data "aws_iam_policy_document" "lambda_cw_events_invocation" {
  statement {
    actions = [
      "lambda:InvokeFunction"
    ]

    resources = [aws_lambda_function.twitter_notifier_lambda.arn]
  }
}






