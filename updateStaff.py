import base64
import hashlib
import hmac
import json, boto3
import os
from time import time
from botocore.exceptions import ClientError

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

    elif user.get("customer_id"):
        return {"statusCode": 403, "body": "forbidden"}    

    body = json.loads(event.get("body", "{}"))
    tenant_id = event["pathParameters"]["tenant_id"]
    staff_id = event["pathParameters"]["staff_id"]
    now = str(int(time()))
    
    if user.get("role") != "manager":
        if user.get("tenant_id") != tenant_id or user.get("staff_id") != staff_id:
            return {"statusCode": 403, "body": "forbidden"} # no pueden modificar otros staff

    allowed = {"name", "role", "email"}
    update_fields = {k: v for k, v in body.items() if k in allowed}
    if not update_fields:
        return {"statusCode": 400, "body": json.dumps({"error": "no valid fields"})}

    # Mapeamos atributos reservados
    attr_names = {f"#{k}": k for k in update_fields.keys()}

    expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_fields]) + ", updatedAt = :u"
    
    values = {f":{k}": v for k,v in update_fields.items()}
    values[":u"] = now

    table = boto3.resource("dynamodb").Table("dev-t_staff")

    try:
        res = table.update_item(
            Key={"tenant_id": tenant_id, "staff_id": staff_id},
            UpdateExpression=expr,
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=attr_names,
            ConditionExpression="attribute_exists(staff_id)",
            ReturnValues="ALL_NEW"
        )
        return {"statusCode": 200, "body": json.dumps(res["Attributes"])}
    
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 404, "body": json.dumps({"error": "staff not found"})}
        else:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
