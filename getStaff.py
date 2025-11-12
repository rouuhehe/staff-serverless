import json
import os
import boto3
def lambda_handler(event, context):
        body = json.loads(event['body'])
        table_name = os.environ["TABLE_NAME"]
         
        staff_id = body['staff_id']
        tenant_id = body['tenant_id']

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        response = table.get_item(
                Key = {
                    'tenant_id': tenant_id,
                    'staff_id': staff_id
                }
        )

        if 'Item' not in response:
            return {
                "statusCode": 404, 
                "body": json.dumps({"error": "Staff not found"})
            }
        
        return {
            'statusCode': 200,
            'body': {
                'customer': json.dumps(response['Item'])
            }
        }