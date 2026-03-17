import base64
import json
import os
from encryption import Encryption


class Database:
    def __init__(self, db_file: str, encryption: Encryption):
        self.db_file = db_file
        self.encryption = encryption
        self.data = {}

    def load(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, "r") as f:
                encrypted_data = json.load(f)
            iv = encrypted_data.get("iv")
            salt_str = encrypted_data.get("salt")
            encrypted_content = encrypted_data.get("encrypted_data")
            if not all([iv, salt_str, encrypted_content]):
                raise ValueError("Повреждённый файл базы данных")

            # Создаём Encryption с сохранённой солью
            salt = base64.b64decode(salt_str)
            self.encryption = Encryption(self.encryption.master_password, salt)  # Обновляем encryption с солью
            decrypted_data = self.encryption.decrypt(iv, encrypted_content)
            self.data = json.loads(decrypted_data)
        else:
            self.data = {}

    def save(self):
        data_str = json.dumps(self.data)
        encrypted = self.encryption.encrypt(data_str)
        with open(self.db_file, "w") as f:
            json.dump(encrypted, f)

    def add_entry(self, url: str, login: str, password: str):
        if url not in self.data:
            self.data[url] = []
        self.data[url].append({"login": login, "password": password})

    def get_entries(self, url: str):
        return self.data.get(url, [])

    def remove_entry(self, url: str, index: int):
        if url in self.data and 0 <= index < len(self.data[url]):
            del self.data[url][index]
            if not self.data[url]:
                del self.data[url]