import boto3


def create_ignored_keywords_table():
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')

    # Create the DynamoDB table.
    table = dynamodb.create_table(
        TableName='ignored_keywords',
        KeySchema=[
            {
                'AttributeName': 'keyword',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'keyword',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName='ignored_keywords')

    print("Table created successfully.")


def insert_ignored_keywords(keywords):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ignored_keywords')

    with table.batch_writer() as batch:
        for keyword in keywords:
            batch.put_item(Item={'keyword': keyword})

    print("Inserted keywords successfully.")


if __name__ == '__main__':
    try:
        create_ignored_keywords_table()
        print("Created table successfully.")
    except Exception as e:
        print(f"Encountered an error while creating table: {e}")

    ignored_keywords = [
        "haugesund",
        "stord",
        "sveio",
        "bømlo",
        "tysvær",
        "vindafjord",
        "brann",
        "ørland",
        "redningshelikopter rygge",
        "arendal",
        "oslo",
        "bergen",
        "oslofjorden",
        "hvaler",
        "sørlandet",
        "hordaland",
        "vestland",
        "trondheim",
        "kystradio",
        "trafikkontroll",
        "laserkontroll",
        "trafikkulykke",
        "trafikkuhell",
        "påkjørsel",
        "fører av bil",
        "innbrudd",
        "ruspåvirket"
    ]

    try:
        insert_ignored_keywords(ignored_keywords)
    except Exception as e:
        print(f"Encountered an error while inserting keywords: {e}")
