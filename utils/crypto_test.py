from utils.crypto import encrypt
from utils.crypto import decrypt

if __name__ == '__main__':
    pid = "whosbug"
    secret = "secret"
    plain_text = "this is plain_text."
    cipher = encrypt(pid, secret, plain_text)
    plain = decrypt(pid, secret, cipher)
    print(f"cipher text is: {cipher}")
    print(f"plain text is: {plain}")

    url_plain_text = "this is plain_text_url."
    url_cipher = encrypt(pid, secret, url_plain_text, mode="url")
    url_plain = decrypt(pid, secret, url_cipher, mode="url")
    print(f"cipher text is: {url_cipher}")
    print(f"plain text is: {url_plain}")