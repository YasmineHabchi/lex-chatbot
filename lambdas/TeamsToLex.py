import json
import logging
import re
import boto3
from botocore.exceptions import ClientError
import html
import os


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize Lex client
lex_client = boto3.client('lexv2-runtime')
# Initialize Lambda client
lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        text = body.get('text', '')
        user_id = body.get('from', {}).get('id', 'default_user_id')
        logger.info(f"Parsed body: {json.dumps(body)}")
        logger.info(f"Extracted text: {text}")
        logger.info(f"User ID: {user_id}")
    except Exception as e:
        logger.error(f"Error parsing event body: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request format'})
        }

    if not text:
        logger.warning("No text provided in the request")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No text provided'})
        }

    cleaned_text = extract_content(text)
    logger.info(f"Cleaned text: {cleaned_text}")
    #Identification du Intent 
    try:
        logger.info("Sending request to Lex")
        lex_response = lex_client.recognize_text(
            botId=os.environ['ALIAS_ID_BOT_ID'][-10:],
            botAliasId=os.environ['ALIAS_ID_BOT_ID'][:10],
            localeId='en_US',
            sessionId=user_id,
            text=cleaned_text
        )
        logger.info(f"Received Lex response: {json.dumps(lex_response)}")
    except Exception as e:
        logger.error(f"Error interacting with Lex: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error processing request'})
        }

    intent_request = {
        'intent_name': lex_response.get('sessionState', {}).get('intent', {}).get('name'),
        'slots': lex_response.get('sessionState', {}).get('intent', {}).get('slots', {}),
        'session_state': lex_response.get('sessionState', {})
    }
    logger.info(f"Intent Request: {json.dumps(intent_request)}")
    
    
    
    
    lex_message = lex_response.get('messages', [{'content': "I'm sorry, I didn't understand that request."}])[0]['content']
    logger.info(f"Lex message: {lex_message}")
    slots = intent_request['slots']
    logger.debug(f"Cleaned Slots: {json.dumps(slots)}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'type': 'message',
            'text': lex_message
        })
    }

def extract_content(input_string):
    match = re.search(r'&nbsp;(.*?)</p>', input_string)
    if match:
        return match.group(1).strip()
    else:
        return None
