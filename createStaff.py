import json, boto3, uuid
from time import time

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    tenant_id = event["pathParameters"]["tenant_id"]

    staff_id = str(uuid.uuid4())
    now = str(int(time()))

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("t_staff")

    staff_data = {
        "tenant_id": tenant_id,
        "staff_id": staff_id,
        "name": body["name"],
        "email": body["email"].lower(),
        "role": body["role"],
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
    }

    table.put_item(Item=staff_data)

    return {
        "statusCode": 201,
        "body": json.dumps({"message": "Staff created", "staff_id": staff_id}),
    }



