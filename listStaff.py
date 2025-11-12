import os
import boto3, json

def lambda_handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]
    table_name = os.environ["TABLE_NAME"]
    table = boto3.resource("dynamodb").Table(table_name)

    res = table.query(
        KeyConditionExpression="tenant_id = :t",
        ExpressionAttributeValues={":t": tenant_id}
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"staff": res["Items"]})
    }