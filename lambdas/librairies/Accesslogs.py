import json
import logging
import time
from datetime import datetime
import boto3
import requests
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')
logs_client = boto3.client('logs')
LOG_STREAMS_BUCKET = os.environ['LOG_STREAMS_BUCKET']

def wait_for_export_task(task_id):
    while True:
        response = logs_client.describe_export_tasks(taskId=task_id)
        status = response['exportTasks'][0]['status']['code']
        if status == 'COMPLETED':
            return True
        elif status in ['CANCELLED', 'FAILED']:
            logger.error(f"Export task {task_id} {status}")
            return False
        time.sleep(30)  # Increase sleep duration

def check_and_cancel_existing_export_tasks(log_group_name):
    try:
        response = logs_client.describe_export_tasks(
            statusCode='RUNNING'
        )
        tasks_to_cancel = [task for task in response['exportTasks'] if task['logGroupName'] == log_group_name]
        
        for task in tasks_to_cancel:
            task_id = task['taskId']
            logger.info(f"Cancelling existing export task: {task_id}")
            logs_client.cancel_export_task(taskId=task_id)
            
            while True:
                task_status = logs_client.describe_export_tasks(taskId=task_id)['exportTasks'][0]['status']['code']
                if task_status in ['CANCELLED', 'COMPLETED', 'FAILED']:
                    break
                time.sleep(2)
            logger.info(f"Export task {task_id} cancelled successfully")
        return len(tasks_to_cancel) > 0
    except Exception as e:
        logger.error(f"Error checking or cancelling export tasks: {str(e)}")
        return False

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))
    try:
        loggroupname = event['LogGroupName']['value']['interpretedValue']
        awsresource = event['awsresource']['value']['interpretedValue']
        starttime = event['StartTime']['value']['interpretedValue']
        endtime = event['EndTime']['value']['interpretedValue']
        log = '/aws/' + awsresource + '/' + loggroupname
        
        start_timestamp = int(datetime.strptime(starttime, '%Y-%m-%d').timestamp() * 1000)
        end_timestamp = int(datetime.strptime(endtime, '%Y-%m-%d').timestamp() * 1000)
        
        # Check and cancel any existing export tasks
        tasks_cancelled = check_and_cancel_existing_export_tasks(log)
        if tasks_cancelled:
            logger.info("Cancelled existing export tasks")
        
        # Create new export task
        export_task_response = logs_client.create_export_task(
            logGroupName=log,
            fromTime=start_timestamp,
            to=end_timestamp,
            destination=LOG_STREAMS_BUCKET,
            destinationPrefix='exported-logs'
        )
        task_id = export_task_response['taskId']
        logger.info(f"Created new export task with ID: {task_id}")

        # Wait for the export task to complete
        if not wait_for_export_task(task_id):
            raise Exception("Export task failed or was cancelled")

        # Generate presigned URLs
        urls = []
        response = s3_client.list_objects_v2(
            Bucket=LOG_STREAMS_BUCKET,
            Prefix=f"exported-logs/{task_id}/"
        )
        for obj in response.get('Contents', []):
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': LOG_STREAMS_BUCKET, 'Key': obj['Key']},
                ExpiresIn=3600
            )
            tiny_url_response = requests.get(f'https://tinyurl.com/api-create.php?url={presigned_url}')
            urls.append(tiny_url_response.text)

        # Format the message to be clear for Lex
        if urls:
            message_content = "Here are the presigned URLs:\n" + "\n".join(urls)
        else:
            message_content = "No log streams were found or there was an issue generating the URLs."

        result = {
            'presigned_urls': urls
        }

        logger.info(f"Returning result: {json.dumps(result)}")
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f"An error occurred: {str(e)}"
            })
        }
