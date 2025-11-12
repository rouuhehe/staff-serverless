import json, boto3
import os
from time import time
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    tenant_id = event["pathParameters"]["tenant_id"]
    staff_id = event["pathParameters"]["staff_id"]
    table_name = os.environ["TABLE_NAME"]
    now = str(int(time()))

    allowed = {"name", "role", "email"}
    update_fields = {k: v for k, v in body.items() if k in allowed}
    if not update_fields:
        return {"statusCode": 400, "body": json.dumps({"error": "no valid fields"})}

    expr = "SET " + ", ".join([f"{k} = :{k}" for k in update_fields]) + ", updatedAt = :u"
    values = {f":{k}": v for k, v in update_fields.items()}
    values[":u"] = now

    table = boto3.resource("dynamodb").Table(table_name)

    try:
        res = table.update_item(
            Key={"tenant_id": tenant_id, "staff_id": staff_id},
            UpdateExpression=expr,
            ExpressionAttributeValues=values,
            ConditionExpression="attribute_exists(staff_id)",
            ReturnValues="ALL_NEW",
        )
        return {"statusCode": 200, "body": json.dumps(res["Attributes"])}
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 404, "body": json.dumps({"error": "staff not found"})}
        else:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
