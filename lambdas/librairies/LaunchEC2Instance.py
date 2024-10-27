import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    print(event)

    instance_type = event['InstanceType']['value']['interpretedValue']
    ami = event['AMI']['value']['interpretedValue']
    key_pair = event['KeyPair']['value']['interpretedValue']
    security_group = event['SecurityGroup']['value']['interpretedValue']
    subnet = event['Subnet']['value']['interpretedValue']

    try:
        # Launching the EC2 instance
        response = ec2.run_instances(
            ImageId=ami,
            InstanceType=instance_type,
            KeyName=key_pair,
            SecurityGroupIds=[security_group],
            SubnetId=subnet,
            MinCount=1,
            MaxCount=1
        )
        instance_id = response['Instances'][0]['InstanceId']

        return {
            'statusCode': 200,
            'body': f'Successfully launched EC2 instance with ID: {instance_id}'
        }

    except ClientError as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
