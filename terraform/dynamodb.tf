# Create a DynamoDB table to store the tweets from the RSS feeds
resource "aws_dynamodb_table" "rss_entries" {
  name         = "rss_entries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# Create a DynamoDB table to store the RSS feeds each user is subscribed to
resource "aws_dynamodb_table" "user_feeds" {
  name         = "user_feeds"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "user"
    type = "S"
  }

  attribute {
    name = "feed_url"
    type = "S"
  }

  hash_key  = "user"
  range_key = "feed_url"

}