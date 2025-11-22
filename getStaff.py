import json
import boto3

def lambda_handler(event, context):
    path = event.get("pathParameters") or {}
    tenant_id = path.get("tenant_id")
    staff_id = path.get("staff_id")

    if not tenant_id or not staff_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "tenant_id and staff_id are required"})
        }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("dev-t_staff")

    response = table.get_item(Key={
        "tenant_id": tenant_id,
        "staff_id": staff_id
    })

    if "Item" not in response:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Staff not found"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps(response["Item"])
    }
