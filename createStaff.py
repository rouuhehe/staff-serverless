import base64
import hashlib
import hmac
import json, boto3, uuid
import os
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
    
    body = json.loads(event.get("body", "{}"))
    tenant_id = event["pathParameters"]["tenant_id"]

    now = str(int(time()))

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    staff_data = {
        "tenant_id": tenant_id,
        "staff_id": body["email"].lower(),
        "name": body["name"],
        "role": body["role"], # manager, repartidor, cocinero, despachador
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
    }

    table.put_item(Item=staff_data)

    return {
        "statusCode": 201,
        "body": json.dumps({"message": "Staff created", "staff_id": body["email"].lower()}),
    }



