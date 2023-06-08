import boto3
import json


def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("ignored_keywords")

    keyword = event['keyword']

    response = table.get_item(Key={"id": "keywords"})
    keywords = response['Item']['keywords']

    if keyword not in keywords:
        keywords.append(keyword)
        table.put_item(Item={"id": "keywords", "keywords": keywords})

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully added keyword {keyword}')
    }
