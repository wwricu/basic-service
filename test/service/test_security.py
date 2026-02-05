import base64
import uuid

import bcrypt


def test_bcrypt():
    password = uuid.uuid4().hex
    credential = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    credential = base64.b64encode(credential).decode()
    result = bcrypt.checkpw(password.encode(), base64.b64decode(credential))
    assert result == True
