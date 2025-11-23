import base64
from datetime import time
import hashlib
import hmac
import json
import os
import boto3

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
    
    path = event.get("pathParameters") or {}
    tenant_id = path.get("tenant_id")
    staff_id = path.get("staff_id")

    if not tenant_id or not staff_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "tenant_id and staff_id are required"})
        }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["TABLE_NAME"])

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
