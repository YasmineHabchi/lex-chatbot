import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    lambda_client = boto3.client('lambda')
    print(event)

    # Extracting slots from the event
    slots = event['sessionState']['intent']['slots']

    #adding accounts
    accountList = {"move2aws": "897652382521"}
    slots['accountList'] = accountList

    interpretations = event['interpretations']
    IntentName = interpretations[0]['intent']['name']

    try:
        # Invoking the second Lambda function
        response = lambda_client.invoke(
            FunctionName=IntentName,
            InvocationType='RequestResponse',
            Payload=json.dumps(slots)
        )

        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            message = response_payload['body']
        else:
            message = f"Error: {response_payload['body']}"

        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": IntentName,
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": message
                }
            ]
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
