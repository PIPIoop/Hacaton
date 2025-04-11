from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Каталогу, для хранения данных профиля: "chrome_profile"
profile_path = os.path.join(os.getcwd(), "chrome_profile")

# Автоматическая установка ChromeDriver
service = Service(ChromeDriverManager().install())

FIXED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Настройки Chrome
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={FIXED_USER_AGENT}")
options.add_argument("--start-maximized")  # Запуск в полноэкранном режиме

# Используем постоянное хранилище профиля
options.add_argument(f"--user-data-dir={profile_path}")

# Инициализация драйвера
driver = webdriver.Chrome(service=service, options=options)

# Открываем WhatsApp Web
driver.get("https://web.whatsapp.com")
print("Если это первый запуск, отсканируйте QR-код. В последующих запусках авторизация будет сохранена.")

# Если сессия уже сохранена, можно добавить ожидание для загрузки чатов
try:
    # Ждем появления списка чатов (или любого другого элемента, свидетельствующего об авторизации)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="listitem"]'))
    )
except Exception as e:
    print("Ошибка при ожидании загрузки чатов:", e)
    driver.quit()
    exit()

contact_name = input("Введите пользователя: ")

try:
    chat = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, f'//span[contains(@title,"{contact_name}")]'))
    )
    chat.click()
    print(f"Чат с '{contact_name}' открыт")
except Exception as e:
    raise Exception(f"Чат с {contact_name} не найден {str(e)}.")

# Ожидаем загрузку сообщений
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="application"]'))
    )
    # Собираем все сообщения
    messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')

    # Выводим текст сообщений
    for i, msg in enumerate(messages, 1):
        print(f"{i}. {msg.text}")

except Exception as e:
    print("Ошибка при получении сообщений:", str(e))

# Закрываем браузер через 5 секунд
time.sleep(5)
driver.quit()
