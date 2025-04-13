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
#Учебный чат Прогресс Агро
# Прокручиваем чат вверх, пока не загрузятся все сообщения
old_message_count = 0
while True:
    messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
    current_count = len(messages)
    if current_count == old_message_count:
        break  # Больше новых сообщений не подгружается
    old_message_count = current_count
    # Прокручиваем контейнер вверх
    driver.execute_script("arguments[0].scrollTop = 0;", chat_container)
    time.sleep(2)  # Ждём подгрузки новых сообщений

# Регулярное выражение для извлечения времени (например, [12:34, ...])
time_pattern = re.compile(r"\[(\d{1,2}:\d{2}),")

# Собираем все сообщения после полной загрузки
messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
print(f"\nНайдено сообщений: {len(messages)}\n")

# Список слов для фильтрации, которые заданы прямо в коде (без ввода с консоли)
filter_words = ["га", "аор", "тск", "мир", "восход", "ао кропоткинское",
                "колхоз прогресс", "сп коломейцево", "по", "отд"]

# Фильтрация сообщений:
# Для каждого фильтруемого слова создаётся регулярное выражение с границами слова (\b) для точного сопоставления.
filtered_count = 0
for i, msg in enumerate(messages, 1):
    msg_text = msg.text
    pre_text = msg.get_attribute("data-pre-plain-text")
    time_str = ""
    if pre_text:
        match = time_pattern.search(pre_text)
        if match:
            time_str = match.group(1)

    msg_text_lower = msg_text.lower()

    # Проверяем наличие хотя бы одного фильтруемого слова как целого слова в тексте
    match_found = False
    for word in filter_words:
        # Формируем регулярное выражение для точного поиска
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, msg_text_lower):
            match_found = True
            break

    if match_found:
        filtered_count += 1
        print(f"{filtered_count}. Время: {time_str}\nСообщение:\n{msg_text}\n")

if filtered_count == 0:
    print("Сообщения, содержащие заданные слова, не найдены.")

# Закрываем браузер через 5 секунд
time.sleep(5)
driver.quit()
