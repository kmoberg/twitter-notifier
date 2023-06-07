# Twitter Notifer

In 2014 when Norwegian government services like police and fire departments moved to TETRA based communication, 
it became impossible for outsiders to listen in using tools such as radio scanners to keep up with what they are doing 
throughout the day. Many of them moved to announcing their operations on Twitter instead. With the takeover of Twitter 
by Elon, I've wanted a way to keep up with what is happening and getting notifications from these services, 
without having an active Twitter account, or paying the insane pricing for their APIs - so this is the solution.

Thanks to [nitter.net](https://nitter.net) a non-JavaScript, super light-weight Twitter scraper, this is possible! 
Nitter offers a great RSS feed for every profile that we can utilize to trigger actions, which is super helpful, and 
allows us to check the RSS feed every so often, then push out new tweets to devices using [pushover](https://pushover.net).

This tool is built to run as an [AWS Lambda](https://aws.amazon.com/lambda/) function on a trigger using CloudWatch Events. 
There is also a not-maintained version of the code to run it locally if so needed. If you set the Lambda function to 
run every minute, you should stay _well_ within the AWS Free-Tier for all the services used, and the entire project 
_should_ run 24/7, forever, for free. This is no guarantee, but it should, in theory as everything, including 5GB 
of storage in DynamoDB is as of writing, free.


## Requirements
- Python 3.10
- AWS Account
  - AWS Lambda
  - DynamoDB
  - IAM
  - SSM Parameter Store
  - CloudWatch Events
  - CloudWatch Logs
- Pushover API and client key

## Setup
### Using Terraform
1. Install [Terraform](https://www.terraform.io/downloads.html)
2. `cd` into the `terraform` directory
3. Run `terraform init` in the `terraform` directory
4. Run `terraform apply` in the `terraform` directory
5. Done!
6. (Optional) Run `terraform destroy` to remove all resources created by Terraform
7. (Optional) Run `terraform fmt` to format the code
8. (Optional) Run `terraform validate` to validate the code
9. (Optional) Run `terraform plan` to see what will be created/destroyed

### Manually
1. From the console, create a new AWS Lambda function
   - Select Python 3.10 as the runtime
   - Set architecture to `arm64` if you want to save money. It should work fine!
   - Create a new execution role with the following permissions: 
     - _Note: These permissions are WAY to permissive and you should limit them!_
     - `AWSLambdaBasicExecutionRole`
     - `AmazonDynamoDBFullAccess`
     - `AmazonSSMFullAccess`
     - `CloudWatchEventsFullAccess`
     - `CloudWatchLogsFullAccess`
   - Once created, go to configuration and set `Timeout` to 30 seconds
   - Upload the `app.py` file to the function or paste the code directly into `lambda_function.py`
2. Create a new Lambda Layer, and upload the contents of the `requirements.txt` file to it.
   - If you don't know how, Google it.
3. From your computer, create a new DynamoDB table by running `db/generate_dynamodb_table.py`
   - You must have the AWS CLI installed and configured for this to work
4. Create a new SSM Parameter Store parameter with the name `/twitter-notifier/pushover_api_key` and the value of your Pushover API key
5. Create a new SSM Parameter Store parameter with the name `/twitter-notifier/pushover_client_key` and the value of your Pushover client key
6. Create a new CloudWatch Event with the following settings:
   - Event pattern: `rate(1 minute)`
   - Target: The Lambda function you created earlier
7. Done!