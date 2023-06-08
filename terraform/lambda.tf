### LAMBDA FUNCTIONS ###
### APP LAMBDA ###
# Create a ZIP file with the 'app' code
data "archive_file" "app_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/app"
  output_path = "${path.module}/app_lambda.zip"


}

# Create a ZIP file with the requirements/layers
data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "../aws-layers/layers"
  output_path = "${path.module}/lambda_layer.zip"
}

# Create a Lambda Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  filename            = "${path.module}/lambda_layer.zip"
  layer_name          = "TwitterNotifierLayers"
  compatible_runtimes = ["python3.10"]
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
}

# Create the Lambda function for the main app
resource "aws_lambda_function" "twitter_notifier_lambda" {
  function_name    = "twitter_notifier_lambda"
  handler          = "app.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.app_lambda_zip.output_base64sha256
  filename         = data.archive_file.app_lambda_zip.output_path
  layers           = [aws_lambda_layer_version.lambda_layer.arn]
  timeout = 300

  environment {
    variables = {
      DEBUG              = "True"
      USER_AWS_REGION    = var.region
      PUSHOVER_USER_KEY  = var.pushover_user_key
      PUSHOVER_API_TOKEN = var.pushover_api_token
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}

# Create a CloudWatch Event Rule to trigger the Lambda function every minute
resource "aws_cloudwatch_event_rule" "every_minute" {
  name                = "every_minute"
  schedule_expression = "rate(1 minute)"
}

# Create a CloudWatch Event Target to trigger the Lambda function
resource "aws_cloudwatch_event_target" "every_minute" {
  rule      = aws_cloudwatch_event_rule.every_minute.name
  target_id = "lambda_target"
  arn       = aws_lambda_function.twitter_notifier_lambda.arn
}

### COMMON LAMBDA FUNCTIONS ###
# Common resources for new lambda functions
data "archive_file" "common_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/common"
  output_path = "${path.module}/common_lambda.zip"
}

data "archive_file" "common_lambda_layer" {
  type        = "zip"
  source_dir  = "../aws-layers/layers/"
  output_path = "${path.module}/common_lambda_layer.zip"
}

resource "aws_lambda_layer_version" "common_lambda_layer" {
  filename            = "${path.module}/common_lambda_layer.zip"
  layer_name          = "CommonLambdaLayers"
  compatible_runtimes = ["python3.10"]
  source_code_hash    = data.archive_file.common_lambda_layer.output_base64sha256
}

### ADD_FEED LAMBDA ###
# Add_feed lambda function
data "archive_file" "add_feed_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/add_feed"
  output_path = "${path.module}/add_feed_lambda.zip"
}

resource "aws_lambda_function" "add_feed_lambda" {
  function_name    = "add_feed_lambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.add_feed_lambda_zip.output_base64sha256
  filename         = data.archive_file.add_feed_lambda_zip.output_path
  layers           = [aws_lambda_layer_version.common_lambda_layer.arn]

  environment {
    variables = {
      DEBUG = "False"
      USER_AWS_REGION = var.region
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}

### ADD_KEYWORD LAMBDA ###
# Zip file for add_keyword lambda function
data "archive_file" "add_keyword_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/add_keyword"
  output_path = "${path.module}/add_keyword_lambda.zip"
}

# Add_feed lambda function
resource "aws_lambda_function" "add_keyword_lambda" {
  function_name    = "add_keyword_lambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.add_keyword_lambda_zip.output_base64sha256
  filename         = data.archive_file.add_keyword_lambda_zip.output_path
  layers           = [aws_lambda_layer_version.common_lambda_layer.arn]

  environment {
    variables = {
      DEBUG = "False"
      USER_AWS_REGION = var.region
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}

### GET_TWEETS LAMBDA ###
# Zip file for get_tweets lambda function
data "archive_file" "get_tweets_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/get_tweets"
  output_path = "${path.module}/get_tweets_lambda.zip"
}

# Add_feed lambda function
resource "aws_lambda_function" "get_tweets_lambda" {
  function_name    = "get_tweets_lambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.get_tweets_lambda_zip.output_base64sha256
  filename         = data.archive_file.get_tweets_lambda_zip.output_path
  layers           = [aws_lambda_layer_version.common_lambda_layer.arn]

  environment {
    variables = {
      DEBUG = "False"
      USER_AWS_REGION = var.region
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}

### ADD_KEYWORD LAMBDA ###
# Zip file for add_keyword lambda function
data "archive_file" "remove_keyword_lambda_zip" {
  type        = "zip"
  source_dir  = "../app/remove_keyword"
  output_path = "${path.module}/remove_keyword_lambda.zip"
}

# Add_feed lambda function
resource "aws_lambda_function" "remove_keyword_lambda" {
  function_name    = "remove_keyword_lambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = data.archive_file.remove_keyword_lambda_zip.output_base64sha256
  filename         = data.archive_file.remove_keyword_lambda_zip.output_path
  layers           = [aws_lambda_layer_version.common_lambda_layer.arn]

  environment {
    variables = {
      DEBUG = "False"
      USER_AWS_REGION = var.region
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_exec]
}