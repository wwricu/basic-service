import hashlib

from service import SecurityService


def generate_password(raw_password: str):
    password: bytes = hashlib.sha256(raw_password.encode()).hexdigest().encode()
    password_hash: bytes = SecurityService.get_password_hash(password)
    print(f"""raw password: {password},\n password_hash: {password_hash}""")
    assert SecurityService.verify_password(password, password_hash) is True


if __name__ == '__main__':
    input_password = input('input raw password\n')
    generate_password(input_password)
