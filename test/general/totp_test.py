import pyotp
import secrets
import base64

key = base64.b32encode(secrets.token_bytes(nbytes=40)).decode()
print(key, len(key))
key = 'WC5OYIVGJUTJWYGCQF6W74AEXZQGALUM4HMDOVJ3THNRFDSP7WYQVQ3I4E4NAWGW'
totp = pyotp.TOTP(key)
print(totp.verify('034149'))
