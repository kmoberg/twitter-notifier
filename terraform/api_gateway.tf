# API GATEWAY
resource "aws_api_gateway_rest_api" "api" {
  name        = "TwitterNotifierAPI"
  description = "API Gateway for the Twitter Notifier"
}

# API RESOURCES
resource "aws_api_gateway_resource" "add_feed" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "add_feed"
}

resource "aws_api_gateway_resource" "add_keyword" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "add_keyword"
}

resource "aws_api_gateway_resource" "get_tweets" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "get_tweets"
}

resource "aws_api_gateway_resource" "remove_keyword" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "remove_keyword"
}

# API METHODS
resource "aws_api_gateway_method" "add_feed" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.add_feed.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "add_keyword" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.add_keyword.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "get_tweets" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.get_tweets.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "remove_keyword" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.remove_keyword.id
  http_method   = "POST"
  authorization = "NONE"
}

# INTEGRATION WITH LAMBDA
resource "aws_api_gateway_integration" "add_feed" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.add_feed.id
  http_method = aws_api_gateway_method.add_feed.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.add_feed_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "add_keyword" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.add_keyword.id
  http_method = aws_api_gateway_method.add_keyword.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.add_keyword_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "get_tweets" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.get_tweets.id
  http_method = aws_api_gateway_method.get_tweets.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.get_tweets_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "remove_keyword" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.remove_keyword.id
  http_method = aws_api_gateway_method.remove_keyword.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.remove_keyword_lambda.invoke_arn
}

# DEPLOYMENT
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  lifecycle {
    create_before_destroy = true
  }
}

# STAGE
resource "aws_api_gateway_stage" "api_stage" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  stage_name    = "v1"
}

# PERMISSIONS
resource "aws_lambda_permission" "add_feed" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_feed_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "add_keyword" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_keyword_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_tweets" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_tweets_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "remove_keyword" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remove_keyword_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
