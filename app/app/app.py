"""
Lambda function for checking new entries in RSS feeds.
This function is triggered by a CloudWatch event every minute.
The function checks for new entries in the RSS feeds specified in the RSS_FEEDS list.
If a new entry is found, it will be added to the DynamoDB table 'rss_entries'.
The function also checks for keywords in the entry title, and if any of the keywords are
found, the function will not add the entry to the database.
"""

import json
import os
import time
import boto3
import requests

from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from common.init_logging import setup_logger

# Get the logger
logger = setup_logger(__name__)

# Get DEBUG environment variable
DEBUG = os.environ.get("DEBUG", False)

# Set the sleep time between checks
SLEEP_TIME = 60

TABLE_NAME = 'politiloggen-entries'

CURRENT_TIME = time.strftime("%H:%M:%S")


class ApiUnavailableException(Exception):
    """
    Exception for when the API is unavailable.
    """
    pass


def get_parameter(name):
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.
    :param name: The name of the parameter.
    :return: The parameter's value.
    """
    ssm = boto3.client("ssm")

    try:
        response = ssm.get_parameter(Name=name, WithDecryption=True)
    except Exception as error:  # pylint: disable=broad-except
        logger.error(f"Encountered an error while retrieving parameter: {error}")
        return None  # FIXME - Should we return None or raise an exception?
    return response["Parameter"]["Value"]


def fetch_api_data():
    """
    Fetches data from the API.
    :return: The data from the API.
    """

    url = "https://politiloggen-vis-frontend.bks-prod.politiet.no/api/messagethread"
    body = {
        "Category": [
            "Savnet",
            "Redning"
        ],
        "sortByEnum": "Date",
        "sortByAsc": False,
        "timeSpanType": "Custom",
        "dateTimeFrom": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "dateTimeTo": "2099-12-24T23:59:00.000Z",
        "skip": 0,
        "take": 10,
        "district": "Sør-Vest politidistrikt"
    }

    response = requests.post(url, json=body, timeout=10)

    if response.status_code != 200:
        raise ApiUnavailableException(f"{response.status_code}: Failed to fetch data from API: {response.text}")

    return response.json()


def notify(
        title: str,
        message: str,
        user_key: str,
        api_token: str,
        sound: str = "default",
        priority: int = 0,
):
    """
        Sends a push notification via Pushover.
        :param title: The title of the notification.
        :param message: The body of the notification.
        :param user_key: The user key obtained from the Pushover app.
        :param api_token: The API token for your Pushover application.
        """
    logger.info(f"Priority {priority}")

    if priority == 2:
        retry = 120
        expire = 600
    else:
        retry = 0
        expire = 0

        data = {
            "token": api_token,
            "user": user_key,
            "title": title,
            "message": message,
            "sound": sound,
            "priority": priority,
            "retry": retry,
            "expire": expire
        }

    logger.debug(f"Pushover data: {data}")

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json", data=data, timeout=15
        )
        logger.debug(f"Pushover response: {response.text}")
    except requests.exceptions.RequestException as error:
        logger.error(f"Encountered an error while sending push notification: {error}")
        # Return with the error status code so that the Lambda function will be retried
        return error

    if response.status_code != 200:
        logger.error(f"Failed to send push notification: {response.text}")


def create_database(dynamodb, table_name=TABLE_NAME):
    """
    Creates the DynamoDB table if it doesn't already exist.
    :param dynamodb: The DynamoDB resource.
    :param table_name: The name of the table to create.
    :return: 200 if the table exists or was created successfully, 500 otherwise
    """

    # Verify that the table does not exist
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
    except dynamodb.meta.client.exceptions.ResourceNotFoundException as error:
        logger.info(f"Table {table_name} does not exist. Creating table...")

        try:
            # Create the DynamoDB table.
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'thread_id',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'message_id',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'thread_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'message_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'district',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                # ProvisionedThroughput={
                #     'ReadCapacityUnits': 2,
                #     'WriteCapacityUnits': 2
                # },
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'DisctrictIndex',
                        'KeySchema': [
                            {
                                'AttributeName': 'district',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ]
            )

            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

            logger.info(f"Created table {table.table_name} successfully.")
            return 200

        except ClientError as e:
            # Handle specific DynamoDB errors or general AWS service errors
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceInUseException':
                logger.warning("Table already exists. Cannot create the table.")
            else:
                logger.error(f"An error occurred: {e.response['Error']['Message']}")

        except Exception as e:
            # Handle other Python errors
            logger.error(f"An unexpected error occurred: {str(e)}")

    logger.info(f"Table {table_name} already exists.")
    return 200


def store_thread_and_messages(table, thread_entry):
    new_messages = []
    thread_id = thread_entry["id"]
    existing_thread = False

    try:
        # Check if the thread already exists
        response = table.get_item(Key={"thread_id": thread_id, "message_id": thread_id})
        if "Item" in response:
            existing_thread = True
            logger.info(f"Thread {thread_id} already exists in the database")
    except ClientError as error:
        logger.debug(f"Key not found: {error.response['Error']['Message']}")

    for index, message in enumerate(thread_entry["messages"]):
        message_id = message["id"]

        try:
            # Check if the message already exists
            response = table.get_item(Key={"thread_id": thread_id, "message_id": message_id})
            if "Item" not in response:
                item = {
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "text": message["text"],
                    "district": thread_entry["district"],
                    "municipality": thread_entry["municipality"],
                    "isActive": thread_entry["isActive"],
                    "hasImage": message["hasImage"],
                    "createdOn": thread_entry["createdOn"],
                    "updatedOn": thread_entry["updatedOn"],
                    "category": thread_entry["category"],
                }
                table.put_item(Item=item)
                new_message_info = item.copy()
                new_message_info["new_thread"] = not existing_thread and index == 0
                new_messages.append(new_message_info)
                logger.info(f"Stored new message {message_id} in the database")
            else:
                logger.info(f"Message {message_id} already exists in the database")
        except ClientError as error:
            logger.error(f"Error accessing database: {error.response['Error']['Message']}")

    return new_messages


def lambda_handler(context, event):
    """
    The main AWS lambda function handler.
    :param context: The context object. This is not used.
    :param event: The event object. This is not used.
    :return: 200 if the function executed successfully, 500 otherwise
    """

    # Get the service resource.
    dynamodb = boto3.resource("dynamodb")

    # Check if the table exists
    try:
        dynamodb.meta.client.describe_table(TableName=TABLE_NAME)
    except dynamodb.meta.client.exceptions.ResourceNotFoundException as error:
        logger.warning(f"{error}")

        create_database(dynamodb, TABLE_NAME)

    # Select the dynamodb table 'rss_entries'
    table = dynamodb.Table(TABLE_NAME)
    all_new_messages = []

    # Parse the JSON response from the API
    try:
        data = fetch_api_data()
    except ApiUnavailableException as error:
        logger.error(f"{error}")
        return 500

    for entry in data["messageThreads"]:
        new_messages = store_thread_and_messages(table, entry)
        all_new_messages.extend(new_messages)

    # Check how many new messages were found
    new_message_count = len(all_new_messages)

    # Send push notifications for new messages
    for index, message in enumerate(all_new_messages):
        logger.info(f"New message [{index}/{new_message_count}]: {message}")

        # Get Pushover details from SSM Parameter Store
        pushover_user_key = get_parameter("pushover_user_key")
        pushover_api_token = get_parameter("pushover_api_token")

        # Customizing the notification title based on the message type
        title_prefix = "NY ALARM" if message.get("new_thread", False) else "ALARM UPDATE"
        title = f"{title_prefix} - {message['category']}: {message['municipality']}"

        # Adjust sound for multiple notifications to avoid being annoying
        sound = "none" if new_message_count > 1 and index > 0 else "MotorolaAlarm"

        logger.info(f"Alarm sound: {sound}")

        if message.get("new_thread", False):
            # If this is a new thread, we want to send a high priority notification
            # to make sure the user sees it
            alarm_priority = 2
        else:
            # If this is an update to an existing thread, we want to send a normal priority notification
            # to avoid being annoying
            alarm_priority = 0

        logger.info(f"Alarm priority: {alarm_priority}")

        # Send the push notification
        notify(
            title=title,
            message=message['text'],
            user_key=pushover_user_key,
            api_token=pushover_api_token,
            sound=sound,
            priority=alarm_priority
        )

    # Return success!
    return {"statusCode": 200, "body": json.dumps("Ran successfully!")}


# Run the lambda function locally
if __name__ == "__main__":
    logger.info(lambda_handler(None, None))
