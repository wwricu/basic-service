import hashlib

from service import SecurityService


def generate_password(raw_password: str):
    password: str = hashlib.sha256(raw_password.encode()).hexdigest()
    salt: str = SecurityService.generate_salt()
    password_hash: str = SecurityService.get_password_hash(password, salt)
    print(f"""raw password: {password},
    salt: {salt},\n password_hash: {password_hash}""")
    assert SecurityService.verify_password(
        password, salt, password_hash
    ) is True


def test_password_hash(raw_password: str, salt: str):
    return SecurityService.get_password_hash(raw_password, salt)


if __name__ == '__main__':
    input_password = input('input raw password\n')
    generate_password(input_password)
