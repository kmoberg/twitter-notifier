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
from boto3.dynamodb.conditions import Key

import feedparser

import requests

# Get DEBUG environment variable
DEBUG = os.environ.get("DEBUG", False)

# Get the service resource.
dynamodb = boto3.resource("dynamodb")
ssm = boto3.client("ssm")

# Select the dynamodb table 'rss_entries'
table = dynamodb.Table("rss_entries")

# Select the dynamodb table 'user_feeds'
user_feeds_table = dynamodb.Table("user_feeds")

# Set the sleep time between checks
SLEEP_TIME = 60

# FIXME - Set the user for whom to check RSS feeds
USER = "kmoberg"


def get_parameter(name):
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.
    :param name: The name of the parameter.
    :return: The parameter's value.
    """
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


def notify(
    title: str,
    message: str,
    user_key: str = get_parameter("pushover_user_key"),
    api_token: str = get_parameter("pushover_api_token"),
):
    """
    Sends a push notification via Pushover.
    :param title: The title of the notification.
    :param message: The body of the notification.
    :param user_key: The user key obtained from the Pushover app.
    :param api_token: The API token for your Pushover application.
    """

    data = {"token": api_token, "user": user_key, "title": title, "message": message}

    response = requests.post(
        "https://api.pushover.net/1/messages.json", data=data, timeout=5
    )

    if response.status_code != 200:
        print(f"Failed to send push notification: {response.text}")


def check_entry(entry_id):
    """
    Check if the id of the entry exists in the database.
    :param entry_id: The id of the entry to check
    :return: True if the entry exists in the database, False otherwise
    """
    try:
        # Try to get the item from the DynamoDB table
        response = table.get_item(Key={"id": entry_id})

        # If the item exists in the table, the response will contain an 'Item' key
        if "Item" in response:
            return True

    except Exception as error:  # pylint: disable=broad-except
        print(f"Encountered an error while checking entry: {error}")

    # If the item doesn't exist or any exception occurred, return False
    return False


def get_user_feeds(user):
    """
    Retrieve the feeds associated with a user from the 'user_feeds' table.
    :param user: The user for whom to retrieve the feeds.
    :return: A list of feed URLs.
    """
    response = user_feeds_table.query(
        KeyConditionExpression=Key('user').eq(user)
    )
    return [item['feed_url'] for item in response['Items']]


def lambda_handler(context, event):  # pylint: disable=inconsistent-return-statements, too-many-locals, too-many-branches, too-many-statements, unused-argument
    """
    The main AWS lambda function handler.
    :param context: The context object. This is not used.
    :param event: The event object. This is not used.
    :return: 200 if the function executed successfully, 500 otherwise
    """

    # Get the feeds for the user
    rss_feeds = get_user_feeds(USER)
    for feed_url in rss_feeds:
        # Get the current entries from the RSS feed
        feed = feedparser.parse(feed_url)

        # Get the author of the tweet
        tweet_author = feed.feed.title

        # Get the latest entry
        latest_entry = feed.entries[0]

        # Use a unique key for each feed's last_seen_id
        last_seen_id_key = f"last_seen_id_{feed_url}"

        # Retrieve the last seen entry ID from the database
        try:
            last_seen_id = table.get_item(Key={"id": last_seen_id_key})["Item"]["value"]
        except:  # pylint: disable=bare-except
            last_seen_id = None

        # Check if the latest entry is new
        if latest_entry.id != last_seen_id:
            # Print a log message that no new entry was found
            print(
                "New tweet detected, checking if there might be more entries since the last check"
            )

            # If there is a new entry, retrieve the latest 10 entries
            entries = feed.entries[:10]

            # Reverse the list so that the oldest entry is first
            entries.reverse()

            # Check each entry
            for entry in entries:
                # Debug
                if DEBUG:
                    # Print the entry title
                    print("DEBUG: " + time.strftime("%H:%M:%S") + f" - {entry.title}")

                if check_entry(entry.id):
                    # Print a log message that the entry already exists in the database starting
                    # with the current time in hh:mm:ss format
                    print(
                        time.strftime("%H:%M:%S")
                        + ": Entry already exists in database, continuing to next entry"
                    )

                    # Count the number of entries that already exist in the database
                    # If all entries already exist, there's no need to continue
                    if entries.index(entry) == len(entries) - 1:
                        print("All entries already exist in database, exiting")
                        break
                    continue

                # List of keywords to check for in the entry title
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
                    "sørlandet",
                    "hordaland",
                    "vestland",
                    "trondheim",
                    "kystradio",
                ]

                # If DEBUG is enabled, print the ignored keywords
                if DEBUG:
                    print(
                        "DEBUG: "
                        + time.strftime("%H:%M:%S")
                        + " - Ignored keywords: "
                        + str(ignored_keywords)
                    )

                # Initialize a flag for ignored keywords
                contains_ignored_keyword = False

                # Iterate over the keywords
                for keyword in ignored_keywords:
                    # Check if the keyword is in the entry title
                    if keyword in entry.title.lower():
                        # Print a log message with the ignored keyword
                        print(
                            f"Entry contains ignored keyword '{keyword}', continuing to next entry"
                        )
                        contains_ignored_keyword = True
                        break

                if contains_ignored_keyword:
                    continue

                # Check if the entry is a retweet
                if entry.title.startswith("RT"):
                    print("Entry is a retweet, continuing to next entry")
                    continue

                # Check if the entry is a reply
                if entry.title.startswith("R to @"):
                    print("Entry is a reply, continuing to next entry")
                    continue

                # Print a log message with the entry title
                print(f"New entry found: {entry.published} - {entry.title}")

                # Generate the texts for the notification
                notification_author = f"New Tweet from {entry.author}"
                notification_text = f"{entry.title}\n({entry.published})\n{entry.link}"
                notification_subtitle = f"Published: {entry.published}"

                # Send the notification
                try:
                    notify(title=notification_author, message=notification_text)
                    # notify_local(title=notification_author, text=notification_text,
                    # subtitle="Test", tweet_url=notification_url)

                    # Log the notification
                    print(
                        f"Sent notification: {notification_author}: {notification_text} - "
                        f"{notification_subtitle}"
                    )
                except Exception as error:  # pylint: disable=broad-except
                    print(f"Encountered an error while sending notification: {error}")

                # Add the new tweet to the database
                try:
                    # Add the entry id to the database
                    table.put_item(Item={"id": entry.id})
                    print(f"Added entry to database: {entry.id}")

                except Exception as error:  # pylint: disable=broad-except
                    print(
                        f"Encountered an error while adding entry to database: {error}"
                    )

                    return {
                        "statusCode": 500,
                        "body": json.dumps(
                            f"Encountered an error while adding entry to "
                            f"database: {error}"
                        ),
                    }

            # Update the last seen entry ID in the database to the latest entry
            try:
                table.put_item(Item={"id": last_seen_id_key, "value": latest_entry.id})
            except Exception as error:  # pylint: disable=broad-except
                print(
                    f"Encountered an error while updating {last_seen_id_key} to database: {error}"
                )

                return {
                    "statusCode": 500,
                    "body": json.dumps(
                        f"Encountered an error while updating "
                        f"{last_seen_id_key} to database: {error}"
                    ),
                }

        else:
            print(
                time.strftime("%H:%M:%S")
                + f": No new entry found for {tweet_author}. Last seen entry ID: {last_seen_id}"
            )

    return {"statusCode": 200, "body": json.dumps("Ran successfully!")}
