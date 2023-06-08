import boto3
import json


def lambda_handler(event, context):
    """
    This function adds a new RSS feed to the user_feeds table in DynamoDB.
    :param event:  The event data from the Lambda trigger.
    :param context:  The context data from the Lambda trigger.
    :return: A message indicating the success or failure of the function.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("user_feeds")

    body = json.loads(event['body'])
    user_id = body['user_id']
    feed_url = body['feed_url']

    table.put_item(Item={"user": user_id, "feed_url": feed_url})

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully added {feed_url} for user {user_id}')
    }
