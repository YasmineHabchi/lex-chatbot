import json
import boto3

def lambda_handler(event, context):
    accountName = event['AccountName']['value']['interpretedValue']
    accountList = event['accountList']
    
    if accountName != "sandbox":
        try:
            sts_client = boto3.client('sts')
            assumed_role = sts_client.assume_role(
                RoleArn=f"arn:aws:iam::{accountList[accountName]}:role/AccessForLexBot",
                RoleSessionName="AssumeRoleSession"
            )

            credentials = assumed_role['Credentials']

            s3 = boto3.client(
                's3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            response = s3.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]

            return {
                'statusCode': 200,
                'body': json.dumps(buckets)
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error: {str(e)}")
            }
        
    try:
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        
        return {
            'statusCode': 200,
            'body': json.dumps(buckets)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
