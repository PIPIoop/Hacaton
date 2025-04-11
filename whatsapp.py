from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Автоматическая установка ChromeDriver
service = Service(ChromeDriverManager().install())

FIXED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Настройки Chrome
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={FIXED_USER_AGENT}")
options.add_argument("--start-maximized")  # Запуск в полноэкранном режиме


# Инициализация драйвера
driver = webdriver.Chrome(service=service, options=options)

# Открываем WhatsApp Web
driver.get("https://web.whatsapp.com")
print("Отсканируйте QR-код в течение 30 секунд...")


#try:
 #  button = WebDriverWait(driver,20 ).until(
  #      EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/span[2]/div/div/div/div/div/div/div[2]/div/button/div/div")]'))
   # )
   #button.click()
#except Exception as e:
 #   print("Кнопка не найдена:", e)
input("НАЖМИТЕ Enter, после авторизации")

# Ожидание авторизации (ручное сканирование QR)
try:
    # Ждем появления списка чатов
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="listitem"]'))
    )
except:
    print("Авторизация не выполнена!")
    driver.quit()
    exit()


contact_name=input("Введите пользователя")


try:
    chat=WebDriverWait(driver,20).until(
        EC.element_to_be_clickable((By.XPATH,f'//span[contains(@title,"{contact_name}")]'))
    )
    chat.click()
    print(f"Чат с '{contact_name} открыт'")
except Exception as e:
    raise Exception(f"Чат с {contact_name} не найден {str(e)}.")




try:
    chat = driver.find_element(
        By.XPATH,
        f'//span[@title="{contact_name}"]'
    )
    chat.click()
except:
    print(f"Чат с '{contact_name}' не найден!")
    driver.quit()
    exit()

# Получаем сообщения
try:
    # Ждем загрузки сообщений
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="application"]'))
    )

  # Собираем все сообщения
    messages = driver.find_elements(
       By.XPATH,
       '//div[contains(@class, "copyable-text")]'
    )

  # Выводим текст сообщений
    for i, msg in enumerate(messages, 1):
        print(f"{i}. {msg.text}")

except Exception as e:
    print("Ошибка при получении сообщений:", str(e))

# Закрываем браузер через 5 секунд
time.sleep(5)
driver.quit()