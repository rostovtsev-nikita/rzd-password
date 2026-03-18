import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
    QLineEdit
)
from PyQt6.QtCore import Qt
from database import Database
from encryption import Encryption


class PasswordManagerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.master_password, ok = QInputDialog.getText(
            self, "Мастер-пароль", "Введите мастер-пароль:", QLineEdit.EchoMode.Password
        )
        if not ok or not self.master_password:
            sys.exit()

        self.encryption = Encryption(self.master_password)
        self.db = Database("passwords.db", self.encryption)
        try:
            self.db.load()
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", f"Неверный мастер-пароль или повреждённые данные: {str(e)}")
            sys.exit()

        self.setWindowTitle("РЖД-Пароли")
        self.layout = QVBoxLayout()

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["URL", "Логин", "Пароль"])
        self.layout.addWidget(self.table)

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_entry)
        self.layout.addWidget(btn_add)

        btn_save = QPushButton("Сохранить изменения")
        btn_save.clicked.connect(self.save_changes)
        self.layout.addWidget(btn_save)

        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self.delete_entry)
        self.layout.addWidget(btn_delete)

        btn_show = QPushButton("Показать пароль")
        btn_show.clicked.connect(self.show_password)
        self.layout.addWidget(btn_show)

        btn_edit_password = QPushButton("Изменить пароль")
        btn_edit_password.clicked.connect(self.edit_password)
        self.layout.addWidget(btn_edit_password)

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.login)
        self.layout.addWidget(btn_login)

        self.setLayout(self.layout)
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        for url, creds in self.db.data.items():
            for entry in creds:
                row = self.table.rowCount()
                self.table.insertRow(row)
                url_item = QTableWidgetItem(url)
                url_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # URL не редактируемый
                self.table.setItem(row, 0, url_item)
                login_item = QTableWidgetItem(entry["login"])
                login_item.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 1, login_item)
                password_item = QTableWidgetItem("••••••••")
                password_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                password_item.setData(Qt.ItemDataRole.UserRole, entry["password"])
                self.table.setItem(row, 2, password_item)

    def add_entry(self):
        url, ok = QInputDialog.getText(self, "URL", "Введите URL:")
        if not ok: return
        login, ok = QInputDialog.getText(self, "Login", "Введите логин:")
        if not ok: return
        password, ok = QInputDialog.getText(
            self, "Password", "Введите пароль:", QLineEdit.EchoMode.Password
        )
        if not ok: return
        if not url.strip() or not login.strip() or not password:
            QMessageBox.warning(self, "Ошибка", "URL, логин и пароль не должны быть пустыми.")
            return
        self.db.add_entry(url, login, password)
        self.db.save()
        self.refresh_table()

    def save_changes(self):
        # Обновляем db.data на основе таблицы и сохраняем скрытые пароли, если пользователь их не менял.
        new_data = {}
        for row in range(self.table.rowCount()):
            url = self.table.item(row, 0).text()
            login = self.table.item(row, 1).text()
            password_item = self.table.item(row, 2)
            password_text = password_item.text()
            original_password = password_item.data(Qt.ItemDataRole.UserRole)

            if password_text == "••••••••":
                password = original_password
            else:
                password = password_text

            if url and login and password:
                if url not in new_data:
                    new_data[url] = []
                new_data[url].append({"login": login, "password": password})

        self.db.data = new_data
        self.db.save()
        self.refresh_table()
        QMessageBox.information(self, "Сохранение", "Изменения сохранены!")

    def delete_entry(self):
        row = self.table.currentRow()
        if row < 0:
            return
        url = self.table.item(row, 0).text()
        login = self.table.item(row, 1).text()
        password_item = self.table.item(row, 2)
        password = password_item.data(Qt.ItemDataRole.UserRole)
        # Ищем индекс внутри конкретного URL, а не в глобальной таблице.
        entry_index = None
        for i, entry in enumerate(self.db.get_entries(url)):
            if entry["login"] == login and entry["password"] == password:
                entry_index = i
                break

        if entry_index is None:
            QMessageBox.warning(self, "Удаление", "Не удалось определить запись для удаления.")
            return

        self.db.remove_entry(url, entry_index)
        self.db.save()
        self.refresh_table()
        QMessageBox.information(self, "Удаление", "Запись удалена!")

    def show_password(self):
        row = self.table.currentRow()
        if row < 0: return
        url = self.table.item(row, 0).text()
        login = self.table.item(row, 1).text()
        for entry in self.db.get_entries(url):
            if entry["login"] == login:
                QMessageBox.information(self, "Пароль", entry["password"])

    def edit_password(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Изменить пароль", "Выберите запись для изменения.")
            return

        current_password = self.table.item(row, 2).data(Qt.ItemDataRole.UserRole)
        new_password, ok = QInputDialog.getText(
            self, "Изменить пароль", "Введите новый пароль:", QLineEdit.EchoMode.Password, current_password
        )
        if not ok:
            return
        if not new_password:
            QMessageBox.warning(self, "Изменить пароль", "Пароль не должен быть пустым.")
            return

        password_item = self.table.item(row, 2)
        password_item.setText("••••••••")
        password_item.setData(Qt.ItemDataRole.UserRole, new_password)

    def login(self):
        row = self.table.currentRow()
        if row < 0: return
        url = self.table.item(row, 0).text()
        login = self.table.item(row, 1).text()
        password = None
        for entry in self.db.get_entries(url):
            if entry["login"] == login:
                password = entry["password"]
        if password:
            try:
                from browser_integration import auto_login
                auto_login(url, login, password)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка входа", f"Не удалось выполнить вход: {str(e)}\nУбедитесь, что chromedriver установлен и в PATH.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PasswordManagerUI()
    window.show()
    sys.exit(app.exec())