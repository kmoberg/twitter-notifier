import json
import os
import time
import pync

import boto3
import feedparser

import requests

# Get DEBUG environment variable
DEBUG = os.environ.get('DEBUG', False)

# Get the service resource.
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

# Select the dynamodb table 'rss_entries'
table = dynamodb.Table('rss_entries')

# Set the sleep time between checks
SLEEP_TIME = 60

# List of RSS feeds to check
RSS_FEEDS = ['https://nitter.net/politietsorvest/rss',
             'https://nitter.net/HRSSorNorge/rss'
             ]


def get_parameter(name):
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.
    :param name: The name of the parameter.
    :return: The parameter's value.
    """
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def notify_local(title: object,
                 text: object,
                 subtitle: object = None,
                 sound: object = "hero",
                 app_icon: object = "https://tweet-notifications.s3.eu-north-1.amazonaws.com/tweet.png",
                 tweet_url: object = None) -> object:
    """
    Uses macOS's built-in notification system to send a notification. Runs an AppleScript command to send the
    notification. See the static "CMD" for the AppleScript command.
    :param title: The title of the notification - is displayed in bold text at the top of the notification
    :param text: The text of the notification - is displayed below the title
    :param subtitle: The subtitle of the notification - is displayed below the title - usually the date and time
    :param sound: Whether to play a specific sound when sending the notification - defaults to "default"
    :param app_icon: Set the icon of the notification - defaults to the Twitter logo
    :param tweet_url: The URL to the tweet to open when clicking the notification
    :return: None
    """
    pync.notify(message=text,
                title=title,
                subtitle=subtitle,
                sound=sound,
                open=tweet_url,
                appIcon=app_icon,
                sender='org.mozilla.firefoxdeveloperedition'
                )


def notify(title: str, message: str, user_key: str = None, api_token: str = None):
    """
    Sends a push notification via Pushover.
    :param title: The title of the notification.
    :param message: The body of the notification.
    :param user_key: The user key obtained from the Pushover app.
    :param api_token: The API token for your Pushover application.
    """

    # Get the user key and API token from AWS Systems Manager Parameter Store if not provided
    if user_key is None:
        user_key = get_parameter('pushover_user_key')
    if api_token is None:
        api_token = get_parameter('pushover_api_token')

    data = {
        "token": api_token,
        "user": user_key,
        "title": title,
        "message": message
    }

    response = requests.post("https://api.pushover.net/1/messages.json", data=data)

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
        response = table.get_item(Key={'id': entry_id})

        # If the item exists in the table, the response will contain an 'Item' key
        if 'Item' in response:
            return True

    except Exception as e:
        print(f"Encountered an error while checking entry: {e}")

    # If the item doesn't exist or any exception occurred, return False
    return False


def lambda_handler(event, context):
    for feed_url in RSS_FEEDS:

        # Get the current entries from the RSS feed
        feed = feedparser.parse(feed_url)

        # Get the author of the tweet
        tweet_author = feed.feed.title

        # Get the latest entry
        latest_entry = feed.entries[0]

        # Use a unique key for each feed's last_seen_id
        last_seen_id_key = f'last_seen_id_{feed_url}'

        # Retrieve the last seen entry ID from the database
        try:
            last_seen_id = table.get_item(Key={'id': last_seen_id_key})['Item']['value']
        except:
            last_seen_id = None

        # Check if the latest entry is new
        if latest_entry.id != last_seen_id:
            # Print a log message that no new entry was found
            print("New tweet detected, checking if there might be more entries since the last check")

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
                    # Print a log message that the entry already exists in the database starting with the current
                    # time in hh:mm:ss format
                    print(time.strftime("%H:%M:%S") + ": Entry already exists in database, continuing to next entry")

                    # Count the number of entries that already exist in the database
                    # If all entries already exist, there's no need to continue
                    if entries.index(entry) == len(entries) - 1:
                        print("All entries already exist in database, exiting")
                        break
                    continue

                # List of keywords to check for in the entry title
                ignored_keywords = ['haugesund', 'stord', 'sveio',
                                    'bømlo', 'tysvær', 'vindafjord', 'brann',
                                    'ørland', 'redningshelikopter rygge',
                                    'arendal', 'oslo', 'bergen', 'oslofjorden',
                                    'sørlandet', 'hordaland', 'vestland', 'trondheim',
                                    ]

                # If DEBUG is enabled, print the ignored keywords
                if DEBUG:
                    print("DEBUG: " + time.strftime("%H:%M:%S") + " - Ignored keywords: " + str(ignored_keywords))

                # Initialize a flag for ignored keywords
                contains_ignored_keyword = False

                # Iterate over the keywords
                for keyword in ignored_keywords:
                    # Check if the keyword is in the entry title
                    if keyword in entry.title.lower():
                        # Print a log message with the ignored keyword
                        print(f"Entry contains ignored keyword '{keyword}', continuing to next entry")
                        contains_ignored_keyword = True
                        break

                if contains_ignored_keyword:
                    continue

                # Check if the entry is a retweet
                if entry.title.startswith('RT'):
                    print("Entry is a retweet, continuing to next entry")
                    continue

                # Check if the entry is a reply
                if entry.title.startswith('R to @'):
                    print("Entry is a reply, continuing to next entry")
                    continue

                # Print a log message with the entry title
                print(f"New entry found: {entry.published} - {entry.title}")

                # Check if running on macOS
                if os.uname().sysname == 'Darwin':

                    # Generate the texts for the notification
                    notification_author = f"New Tweet from {entry.author}"
                    notification_text = f"{entry.title}\n({entry.published})\n{entry.link}"
                    notification_subtitle = f"Published: {entry.published}"
                    notification_url = f"{entry.link}"

                    # Send the notification
                    try:
                        notify(title=notification_author, message=notification_text),
                        # notify_local(title=notification_author, text=notification_text, subtitle="Test",
                        #             tweet_url=notification_url)

                        # Log the notification
                        print(
                            f"Sent notification: {notification_author}: {notification_text} - {notification_subtitle}")
                    except Exception as e:
                        print(f"Encountered an error while sending notification: {e}")

                # Add the new tweet to the database
                try:
                    # Add the entry id to the database
                    table.put_item(Item={'id': entry.id})
                    print(f"Added entry to database: {entry.id}")

                    # Check if running in AWS Lambda
                    if os.getenv('AWS_EXECUTION_ENV') is not None:
                        # If there's a new entry, send an SMS via SNS
                        sns = boto3.client('sns')
                        sns.publish(
                            PhoneNumber=os.getenv('PHONE_NUMBER'),
                            Message=f"New RSS Entry: {entry.title}\n{entry.link}"
                        )

                except Exception as e:
                    print(f"Encountered an error while adding entry to database: {e}")

            # Update the last seen entry ID in the database to the latest entry
            try:
                table.put_item(Item={'id': last_seen_id_key, 'value': latest_entry.id})
            except Exception as e:
                print(f"Encountered an error while updating {last_seen_id_key} to database: {e}")

        else:
            print(time.strftime(
                "%H:%M:%S") + f": No new entry found for {tweet_author}. Waiting for {SLEEP_TIME} seconds before next check ")


if __name__ == "__main__":

    # Verify that we're not running in AWS Lambda
    if os.getenv('AWS_EXECUTION_ENV') is not None:
        # Verify that notifications are working
        notify_local(title="Test", text="Test", subtitle="Test",
                     tweet_url="https://nitter.net/politietsorvest/status/1437450000000000000")

        while True:
            lambda_handler(None, None)
            time.sleep(SLEEP_TIME)  # waits for 60 seconds before the next execution
