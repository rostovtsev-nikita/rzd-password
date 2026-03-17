import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def find_element_xpath(driver, possible_xpaths):
    """Пробует несколько XPATH и возвращает первый найденный"""
    wait = WebDriverWait(driver, 5)
    for xpath in possible_xpaths:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return xpath
        except:
            continue
    raise ValueError("Элемент не найден по возможным XPATH")


def auto_login(url, username, password):
    try:
        # Путь к chromedriver рядом с exe/скриптом
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        driver_path = os.path.join(base_dir, "chromedriver.exe")

        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"Не найден chromedriver: {driver_path}")

        service = Service(driver_path)

        # Настройки Chrome
        options = Options()
        options.add_experimental_option("detach", True)  # Не закрывать браузер
        options.add_argument("--start-maximized")
        # Папка для профиля (сохраняет авторизацию)
        profile_dir = os.path.join(os.path.expanduser("~"), "selenium_profile")
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        # Если страница уже авторизована — ничего не делаем
        time.sleep(2)

        # Автопарсинг XPATH для логина
        login_xpaths = [
            "//input[@type='text' or @type='email' or contains(@name,'user') or contains(@id,'user') "
            "or contains(@name,'login') or contains(@id,'login') or contains(@name,'email') or contains(@id,'email')]",
            "//input[@placeholder='Username' or @placeholder='Email' or @placeholder='Login']"
        ]
        login_xpath = find_element_xpath(driver, login_xpaths)

        # Для пароля
        pass_xpaths = [
            "//input[@type='password']",
            "//input[contains(@name,'pass') or contains(@id,'pass')]"
        ]
        pass_xpath = find_element_xpath(driver, pass_xpaths)

        # Для кнопки
        button_xpaths = [
            "//button[@type='submit' or contains(text(),'Login') or contains(text(),'Sign in') "
            "or contains(text(),'Войти') or contains(@value,'Login')]",
            "//input[@type='submit']"
        ]
        button_xpath = find_element_xpath(driver, button_xpaths)

        # Заполнение формы
        driver.find_element(By.XPATH, login_xpath).clear()
        driver.find_element(By.XPATH, login_xpath).send_keys(username)
        driver.find_element(By.XPATH, pass_xpath).clear()
        driver.find_element(By.XPATH, pass_xpath).send_keys(password)
        driver.find_element(By.XPATH, button_xpath).click()

        print("✅ Авторизация завершена. Браузер останется открытым.")
        input("Нажмите Enter, чтобы закрыть браузер...")
        driver.quit()

    except Exception as e:
        raise RuntimeError(f"Ошибка автопарсинга или входа: {str(e)}")
