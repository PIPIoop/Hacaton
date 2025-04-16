from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re


def clean_text(text):
    # Защищаем даты: ДД.ММ.ГГГГ и ДД.ММ.ГГ
    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', r'\1<DOT>\2<DOT>\3', text)
    # Защищаем даты: ДД.ММ (без года)
    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\b', r'\1<DOT>\2', text)
    # Защищаем дефисы между цифрой и буквой
    text = re.sub(r'(\d)-([a-zA-Zа-яА-Я])', r'\1<SAFE_HYPHEN>\2', text)
    # Защищаем слэш между цифрами (например, для дробей или дат)
    text = re.sub(r'(?<=\d)/(?=\d)', r'<SAFE_SLASH>', text)

    # Заменяем все неразрешённые символы на пробел
    text = re.sub(r'[^\w\s<SAFE_HYPHEN><DOT>]', ' ', text)

    # Восстанавливаем дефисы, точки и слэш
    text = text.replace('<SAFE_HYPHEN>', '-').replace('<DOT>', '.').replace('<SAFE_SLASH>', '/')

    # Замена вхождения "попу" в любом регистре на "По Пу"
    text = re.sub(r'(?i)\bпопу\b', 'По Пу', text)

    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Путь к сохранённому профилю
profile_path = os.path.join(os.getcwd(), "chrome_profile")

# Настройка драйвера
service = Service(ChromeDriverManager().install())
FIXED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={FIXED_USER_AGENT}")
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={profile_path}")

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://web.whatsapp.com")
print("Если это первый запуск, отсканируйте QR-код. В последующих запусках авторизация будет сохранена.")

# Ожидание авторизации
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

# Ожидание появления контейнера чата
try:
    chat_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-area")]'))
    )
except Exception as e:
    print("Контейнер сообщений не найден:", e)
    driver.quit()
    exit()

# Прокрутка вверх для загрузки истории
old_message_count = 0
while True:
    messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
    current_count = len(messages)
    if current_count == old_message_count:
        break
    old_message_count = current_count
    driver.execute_script("arguments[0].scrollTop = 0;", chat_container)
    time.sleep(2)

# Регулярные выражения для извлечения служебной информации
pre_text_pattern = re.compile(r"\[(\d{1,2}:\d{2}), (\d{1,2}\.\d{1,2}\.\d{4})] (.*?):")
quote_text_pattern = re.compile(r'^\[\d{1,2}:\d{2}, \d{2}\.\d{2}\.\d{4}] .+?:')

# Слова для фильтрации сообщений
filter_words = [
    "попу", "аор", "тск", "мир", "восход", "ао кропоткинское",
    "колхоз прогресс", "сп коломейцево", "пу", "отд"
]

# Паттерн для поиска даты в сообщении (форматы: ДД.ММ, ДД.ММ.ГГ и ДД.ММ.ГГГГ)
date_pattern = re.compile(r'\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b')

# Сбор сообщений
messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
print(f"\nНайдено сообщений: {len(messages)}\n")

filtered_count = 0
for msg in messages:
    # Пропускаем цитаты (DOM)
    try:
        msg.find_element(By.XPATH, './/div[contains(@data-testid, "quoted-message")]')
        continue
    except:
        pass

    msg_text = msg.text.strip()
    lines = msg_text.splitlines()

    # Пропускаем ручные цитаты
    if len(lines) >= 2 and lines[0].strip() == "Вы" and re.match(r'^\d{1,2}\.\d{1,2}$', lines[1].strip()):
        continue

    if any(quote_text_pattern.match(line.strip()) for line in lines):
        continue

    # Фильтруем по ключевым словам
    msg_text_lower = msg_text.lower()
    if any(re.search(rf"\b{re.escape(word)}\b", msg_text_lower) for word in filter_words):
        pre_text = msg.get_attribute("data-pre-plain-text")
        time_str, date_str, sender = "", "", ""
        if pre_text:
            match = pre_text_pattern.search(pre_text)
            if match:
                time_str = match.group(1)
                date_str = match.group(2)
                sender = match.group(3)

        filtered_count += 1
        # Приводим сообщение к однострочному виду и очищаем его
        msg_single_line = " ".join(msg_text.splitlines())
        msg_single_line = clean_text(msg_single_line)

        # Определяем дату из сообщения; если не найдено – используем "17.04"
        found_date = date_pattern.search(msg_single_line)
        if found_date:
            message_date = found_date.group(0)
        else:
            message_date = "17.04"

        # Если сообщение уже начинается с даты (возможно, с дублированием), убираем лишние вхождения.
        # Используем re.match для поиска повторяющейся последовательности даты в начале строки.
        match = re.match(rf'^(({re.escape(message_date)}\s+)+)', msg_single_line)
        if match:
            # Оставляем остаток строки после блока повторяющейся даты и обрезаем лишние пробелы
            new_message = msg_single_line[match.end():].lstrip()
            output_line = f"{message_date} {new_message}"
        else:
            output_line = f"{message_date} {msg_single_line}"

        try:
            with open('message.txt', 'a', encoding='utf-8') as file:
                file.write(f"{output_line}\n")
                print(f"{filtered_count}. Отправитель: {sender} | Дата: {date_str} {time_str} | Дата из сообщения: {message_date}| Сообщение: {msg_single_line}")
        except FileNotFoundError as e:
            print(e)

if filtered_count == 0:
    print("Сообщения, содержащие заданные слова, не найдены.")

time.sleep(5)
driver.quit()
