import pyotp


totp = pyotp.TOTP('WLBTGZZEYTJMCKCTWY6XWVL3PFKFNRLX')
print(totp.verify('872499'))
