import boto3
import json


def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("ignored_keywords")

    keyword = event['keyword']

    response = table.get_item(Key={"id": "keywords"})
    keywords = response['Item']['keywords']

    if keyword in keywords:
        keywords.remove(keyword)
        table.put_item(Item={"id": "keywords", "keywords": keywords})

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully removed keyword {keyword}')
    }
