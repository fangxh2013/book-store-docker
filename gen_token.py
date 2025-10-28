import secrets
import base64

# 生成 NACOS_AUTH_TOKEN (原始字符串 >= 32 字符)
original_secret = secrets.token_urlsafe(64)  # 48 字符确保解码后 > 32 字节
encoded_token = base64.b64encode(original_secret.encode()).decode()
print("NACOS_AUTH_TOKEN:", encoded_token)
print("Decoded length:", len(base64.b64decode(encoded_token)))

# 生成 NACOS_AUTH_IDENTITY_KEY
original_key = secrets.token_urlsafe(64)
encoded_key = base64.b64encode(original_key.encode()).decode()
print("NACOS_AUTH_IDENTITY_KEY:", encoded_key)
print("Decoded length:", len(base64.b64decode(encoded_key)))

# 生成 NACOS_AUTH_IDENTITY_VALUE
original_value = secrets.token_urlsafe(64)
encoded_value = base64.b64encode(original_value.encode()).decode()
print("NACOS_AUTH_IDENTITY_VALUE:", encoded_value)
print("Decoded length:", len(base64.b64decode(encoded_value)))