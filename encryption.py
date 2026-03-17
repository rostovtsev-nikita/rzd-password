import os
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64


class Encryption:
    def __init__(self, master_password, salt: bytes = None):
        if isinstance(master_password, str):
            self.master_password = master_password.encode()
        else:
            self.master_password = master_password
        if salt is None:
            self.salt = os.urandom(16)
        else:
            self.salt = salt
        self.key = self._derive_key()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = kdf.derive(self.master_password)
        return key

    def encrypt(self, data: str) -> dict:
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        return {
            "iv": base64.b64encode(iv).decode("utf-8"),
            "salt": base64.b64encode(self.salt).decode("utf-8"),
            "encrypted_data": base64.b64encode(encrypted_data).decode("utf-8")
        }

    def decrypt(self, iv: str, encrypted_data: str) -> str:
        iv = base64.b64decode(iv)
        encrypted_data = base64.b64decode(encrypted_data)

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode("utf-8")