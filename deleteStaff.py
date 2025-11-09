import json
import boto3
from botocore.exceptions import ClientError
from time import time

def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("t_staff")

    tenant_id = event["pathParameters"]["tenant_id"]
    staff_id = event["pathParameters"]["staff_id"]
    now = str(int(time()))

    try:
        response = table.update_item(
            Key={
                "tenant_id": tenant_id,
                "staff_id": staff_id
            },
            UpdateExpression="SET isActive = :false, updatedAt = :now",
            ExpressionAttributeValues={
                ":false": False,
                ":now": now
            },
            ConditionExpression="attribute_exists(staff_id)",
            ReturnValues="ALL_NEW"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Staff deactivated successfully",
                "updated": response["Attributes"]
            })
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Staff not found"})
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
