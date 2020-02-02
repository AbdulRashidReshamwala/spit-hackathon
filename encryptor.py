from cryptography.fernet import Fernet
import base64
# key = Fernet.generate_key() #this is your "password"
# print(key)
# with open('.key','wb') as f:
#     f.write(key)
with open('.key','rb') as f:
    key = f.read()
cipher = Fernet(key)
encoded_text = cipher_suite.encrypt("Hello stackoverflow!".encode())
# print(encoded_text)
c = base64.b64encode(encoded_text)
print(c)
decoded_text = cipher_suite.decrypt(base64.b64decode(c))
print(decoded_text.decode())
# d = base64.b64encode(decoded_text)
# print(d)