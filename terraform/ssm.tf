# Create a SSM parameter to store the Pushover user key
resource "aws_ssm_parameter" "pushover_user_key" {
  name  = "/pushover_user_key"
  type  = "SecureString"
  value = var.pushover_user_key
}

# Create a SSM parameter to store the Pushover API token
resource "aws_ssm_parameter" "pushover_api_token" {
  name  = "/pushover_api_token"
  type  = "SecureString"
  value = var.pushover_api_token
}
