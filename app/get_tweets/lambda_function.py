import boto3
import json

from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    """
    This function gets the latest 10 RSS entries from the user_feeds table in DynamoDB.
    :param event:  The event data from the Lambda trigger.
    :param context:  The context data from the Lambda trigger.
    :return:
    """
    dynamodb = boto3.resource("dynamodb")
    user_feeds_table = dynamodb.Table("user_feeds")
    rss_entries_table = dynamodb.Table("rss_entries")

    user_id = event['user_id']

    response = user_feeds_table.query(
        KeyConditionExpression=Key('user').eq(user_id)
    )
    feed_urls = [item['feed_url'] for item in response['Items']]

    entries = []
    for feed_url in feed_urls:
        response = rss_entries_table.query(
            KeyConditionExpression=Key('feed_url').eq(feed_url)
        )
        entries.extend(response['Items'])

    # Sort entries by date, and get the latest ones
    entries.sort(key=lambda x: x['date'], reverse=True)
    latest_entries = entries[:10]

    return {
        'statusCode': 200,
        'body': json.dumps(latest_entries)
    }
