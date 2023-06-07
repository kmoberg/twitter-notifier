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

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.twitter_notifier_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_minute.arn
}


resource "aws_iam_role_policy" "lambda_cw_events_invocation" {
  name   = "lambda_cw_events_invocation"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_cw_events_invocation.json
}



resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

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

resource "aws_iam_policy" "lambda_exec_policy" {
  name = "lambda_exec_policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Sid": "AllowAccessToSpecificParameters",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": [
        "arn:aws:ssm:${var.region}:${var.account_id}:parameter/pushover_user_key",
        "arn:aws:ssm:${var.region}:${var.account_id}:parameter/pushover_api_token"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:${var.region}:${var.account_id}:table/rss_entries"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_exec" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_exec_policy.arn
}




data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../app"
  output_path = "${path.module}/lambda.zip"


}

data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "../aws-layers/layers"
  output_path = "${path.module}/lambda_layer.zip"
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename            = "${path.module}/lambda_layer.zip"
  layer_name          = "TwitterNotifierLayers"
  compatible_runtimes = ["python3.10"]
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
}


resource "aws_lambda_function" "twitter_notifier_lambda" {
  function_name    = "twitter_notifier_lambda"
  handler          = "app.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  filename         = data.archive_file.lambda_zip.output_path
  layers           = [aws_lambda_layer_version.lambda_layer.arn]

  environment {
    variables = {
      DEBUG              = "False"
      USER_AWS_REGION    = var.region
      PUSHOVER_USER_KEY  = var.pushover_user_key
      PUSHOVER_API_TOKEN = var.pushover_api_token
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}

resource "aws_cloudwatch_event_rule" "every_minute" {
  name                = "every_minute"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "every_minute" {
  rule      = aws_cloudwatch_event_rule.every_minute.name
  target_id = "lambda_target"
  arn       = aws_lambda_function.twitter_notifier_lambda.arn
}


resource "aws_dynamodb_table" "rss_entries" {
  name         = "rss_entries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_ssm_parameter" "pushover_user_key" {
  name  = "/pushover_user_key"
  type  = "SecureString"
  value = var.pushover_user_key
}

resource "aws_ssm_parameter" "pushover_api_token" {
  name  = "/pushover_api_token"
  type  = "SecureString"
  value = var.pushover_api_token
}
