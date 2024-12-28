import base64
import hashlib
import hmac


from wwricu.config import AdminConfig, Config


def hmac_sign(plain: str):
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


def hmac_verify(plain: str, sign: str) -> bool:
    if not plain or not sign:
        return False
    return hmac_sign(plain) == sign


secure_key = base64.b64decode(AdminConfig.secure_key.encode(Config.encoding))
