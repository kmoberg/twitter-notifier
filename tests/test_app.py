import unittest
from unittest.mock import patch, Mock
import boto3
from moto import mock_dynamodb, mock_ssm
import json
import os


class TestLambdaFunction(unittest.TestCase):
    @mock_dynamodb
    @mock_ssm
    @patch('feedparser.parse')
    @patch('requests.post')
    def test_lambda_handler(self, mock_requests_post, mock_feedparser_parse):
        # Now import your lambda function script
        import app

        # Mock the SSM parameters
        ssm = boto3.client('ssm')
        ssm.put_parameter(
            Name='pushover_user_key',
            Value='test_pushover_user_key',
            Type='String'
        )
        ssm.put_parameter(
            Name='pushover_api_token',
            Value='test_pushover_api_token',
            Type='String'
        )

        # Mock the DynamoDB tables
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName='rss_entries',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        user_feeds_table = dynamodb.create_table(
            TableName='user_feeds',
            KeySchema=[{'AttributeName': 'user', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )

        # Add some test data to the user_feeds table
        user_feeds_table.put_item(Item={'user': 'kmoberg', 'feed_url': 'http://example.com/rss'})

        # Mock the feedparser.parse method
        mock_feedparser_parse.return_value = {
            'feed': {'title': 'test title'},
            'entries': [{'id': 'test_id', 'title': 'test title', 'published': 'test date', 'link': 'test link'}]
        }

        # Mock the requests.post method
        mock_requests_post.return_value.status_code = 200

        # Call the lambda_handler function
        response = app.lambda_handler({}, {})

        # Assert that the function returned successfully
        self.assertEqual(response, {'statusCode': 200, 'body': json.dumps("Ran successfully!")})

    # Additional test methods would go here to test other aspects of the function


if __name__ == '__main__':
    unittest.main()
