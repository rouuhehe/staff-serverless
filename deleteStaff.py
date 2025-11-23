import os
from botocore.exceptions import ClientError
import base64
import hashlib
import hmac
import json, boto3
from time import time

SECRET_KEY = os.environ["JWT_SECRET"]

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def verify_token(token):
    try:
        header_b64, body_b64, signature = token.split(".")
        expected_sig = b64url_encode(
            hmac.new(SECRET_KEY.encode(), f"{header_b64}.{body_b64}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected_sig, signature):
            return None
        payload = json.loads(b64url_decode(body_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except:
        return None
    

def lambda_handler(event, context):
    headers = event.get("headers", {})
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return {"statusCode": 401, "body": "missing token"}
    token = auth.replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return {"statusCode": 401, "body": "invalid token"}        

    if user.get("tenant_id"):
        if user.get("role") != "manager": # solo managers pueden crear staff
            return {"statusCode": 403, "body": "forbidden"}
    elif user.get("customer_id"):
        return {"statusCode": 403, "body": "forbidden"}    

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["TABLE_NAME"])

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
