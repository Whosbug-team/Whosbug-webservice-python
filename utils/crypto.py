from base64 import b64encode
from base64 import b64decode
from base64 import urlsafe_b64encode
from base64 import urlsafe_b64decode
from ntpath import realpath
from Crypto.Hash import HMAC
from Crypto.Hash import MD5
from Crypto.Hash import SHA256
from Crypto.Cipher import AES

"""
    p.s.
    project_id and project_secret are corresponding.
    Think project_id as public "username".
    Think secret as private "password".
    Cipher is AES-CFB
"""


def generateKIV(project_id: str, secret: str):
    project_id = bytes(project_id, encoding='utf-8')
    secret = bytes(secret, encoding='utf-8')
    # K is 256bits, IV is 16bytes=128bit
    hK = HMAC.new(secret, digestmod=SHA256)
    hIV = HMAC.new(secret, digestmod=MD5)
    hK.update(project_id)
    hIV.update(project_id)
    K = hK.digest()
    IV = hIV.digest()
    return K, IV


def encrypt(project_id: str, secret: str, plain_text: str, mode=None) -> str:
    plain_text = bytes(plain_text, encoding='utf-8')
    K, IV = generateKIV(project_id, secret)
    cipher = AES.new(K, AES.MODE_CFB, IV, segment_size=256)
    cipher_bytes = cipher.encrypt(plain_text)
    # cipher_text contain only ASCII
    if mode == "url":
        return urlsafe_b64encode(cipher_bytes)
    else:
        return b64encode(cipher_bytes)

def decrypt(project_id: str, secret: str, cipher_text: str, mode=None) -> str:
    if mode == "url":
        cipher_text = urlsafe_b64decode(cipher_text)
    else:
        cipher_text = b64decode(cipher_text)
    K, IV = generateKIV(project_id, secret)
    cipher = AES.new(K, AES.MODE_CFB, IV, segment_size=256)
    plain_bytes = cipher.decrypt(cipher_text)
    return plain_bytes.decode('utf-8', 'replace')
