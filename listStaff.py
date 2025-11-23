import base64
import hashlib
import hmac
import os
import time
import boto3, json

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
    if user.get("customer_id"): 
        return {"statusCode": 403, "body": "forbidden"}

    tenant_id = event["pathParameters"]["tenant_id"]
    table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

    res = table.query(
        KeyConditionExpression="tenant_id = :t",
        ExpressionAttributeValues={":t": tenant_id}
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"staff": res["Items"]})
    }
