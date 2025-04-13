from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re

# Указываем путь к каталогу для сохранения данных профиля
profile_path = os.path.join(os.getcwd(), "chrome_profile")

# Автоматическая установка ChromeDriver
service = Service(ChromeDriverManager().install())

FIXED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Настройка Chrome
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={FIXED_USER_AGENT}")
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={profile_path}")

driver = webdriver.Chrome(service=service, options=options)

# Открываем WhatsApp Web
driver.get("https://web.whatsapp.com")
print("Если это первый запуск, отсканируйте QR-код. В последующих запусках авторизация будет сохранена.")

# Ожидание загрузки списка чатов, что говорит об авторизации
try:
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
    raise Exception(f"Чат с {contact_name} не найден. {str(e)}")

# Ожидание загрузки контейнера сообщений (области, где располагаются сообщения)
try:
    chat_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-area")]'))
    )
except Exception as e:
    print("Контейнер сообщений не найден:", e)
    driver.quit()
    exit()

# Прокручиваем чат вверх, пока не загрузятся все сообщения
old_message_count = 0
while True:
    messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
    current_count = len(messages)
    if current_count == old_message_count:
        break
    old_message_count = current_count
    driver.execute_script("arguments[0].scrollTop = 0;", chat_container)
    time.sleep(2)

# Регулярки
time_pattern = re.compile(r"\[(\d{1,2}:\d{2}),")
quote_text_pattern = re.compile(r'^\[\d{1,2}:\d{2}, \d{2}\.\d{2}\.\d{4}] .+?:')

# Слова для фильтрации
filter_words = ["попу","аор", "тск", "мир", "восход", "ао кропоткинское",
                "колхоз прогресс", "сп коломейцево", "пу", "отд"]

messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
print(f"\nНайдено сообщений: {len(messages)}\n")

filtered_count = 0
for msg in messages:
    # 1. DOM-цитата
    try:
        msg.find_element(By.XPATH, './/div[contains(@data-testid, "quoted-message")]')
        continue
    except:
        pass

    msg_text = msg.text.strip()

    #Проверка на "Вы" и дата в следующей строке
    lines = msg_text.splitlines()
    if len(lines) >= 2:
        if lines[0].strip() == "Вы" and re.match(r'^\d{1,2}\.\d{1,2}$', lines[1].strip()):
            continue

    #Проверка на встроенную цитату
    if any(quote_text_pattern.match(line.strip()) for line in lines):
        continue

    # Проверка фильтрации по словам
    msg_text_lower = msg_text.lower()
    if any(re.search(rf"\b{re.escape(word)}\b", msg_text_lower) for word in filter_words):
        pre_text = msg.get_attribute("data-pre-plain-text")
        time_str = ""
        if pre_text:
            match = time_pattern.search(pre_text)
            if match:
                time_str = match.group(1)
        filtered_count += 1
        print(f"{filtered_count}. Время: {time_str}\nСообщение:\n{msg_text}\n")

if filtered_count == 0:
    print("Сообщения, содержащие заданные слова, не найдены.")

time.sleep(5)
driver.quit()
