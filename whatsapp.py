from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import os
import re
from collections import defaultdict
from datetime import datetime
from docx import Document

def clean_text(text):
    # Защищаем даты: ДД.ММ.ГГГГ и ДД.ММ.ГГ
    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', r'\1<DOT>\2<DOT>\3', text)
    # Защищаем даты: ДД.ММ (без года)
    text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\b', r'\1<DOT>\2', text)
    # Защищаем дефисы между цифрой и буквой
    text = re.sub(r'(\d)-([a-zA-Zа-яА-Я])', r'\1<SAFE_HYPHEN>\2', text)
    # Защищаем слэш между цифрами
    text = re.sub(r'(?<=\d)/(?=\d)', r'<SAFE_SLASH>', text)

    # Заменяем все неразрешённые символы на пробел
    text = re.sub(r'[^\w\s<SAFE_HYPHEN><DOT>]', ' ', text)

    # Восстанавливаем спецсимволы
    text = text.replace('<SAFE_HYPHEN>', '-').replace('<DOT>', '.').replace('<SAFE_SLASH>', '/')

    # Замена "попу" -> "По Пу"
    text = re.sub(r'(?i)\bпопу\b', 'По Пу', text)

    # Удаляем лишние пробелы
    return re.sub(r'\s+', ' ', text).strip()

def save_messages_to_word(messages, output_dir='messages'):
    """
    Сохраняет каждое сообщение в отдельный .docx-файл.
    messages: list of dict с ключами 'sender', 'text', 'datetime'
    """
    os.makedirs(output_dir, exist_ok=True)
    counters = defaultdict(int)

    for msg in messages:
        sender = msg['sender']
        text = msg['text']
        dt = msg['datetime']
        counters[sender] += 1

        safe_sender = re.sub(r'[\\/:\*\?"<>|]', '_', sender)
        time_suffix = f"{dt.minute:02d}{dt.hour:02d}{dt.day:02d}{dt.month:02d}{dt.year}"
        filename = f"{safe_sender}_{counters[sender]}_{time_suffix}.docx"
        filepath = os.path.join(output_dir, filename)

        doc = Document()
        doc.add_paragraph(text)
        doc.save(filepath)
        print(f"Сохранено: {filepath}")


# Настройка Selenium и авторизация в WhatsApp Web
profile_path = os.path.join(os.getcwd(), "chrome_profile")
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://web.whatsapp.com")
print("Если первый запуск — отсканируйте QR-код.")

# Ждём загрузки списка чатов
WebDriverWait(driver, 60).until(
    EC.presence_of_element_located((By.XPATH, '//div[@role="listitem"]'))
)

contact_name = input("Введите имя контакта или группы: ")

# Открываем нужный чат
chat = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact_name}"]'))
)
chat.click()
print(f"Чат с '{contact_name}' открыт.")

# Ждём появления контейнера сообщений
chat_container = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-area")]'))
)

# Доскроллим вверх всю историю
old_count = 0
while True:
    msgs = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]')
    if len(msgs) == old_count:
        break
    old_count = len(msgs)
    driver.execute_script("arguments[0].scrollTop = 0;", chat_container)
    time.sleep(1)

# Паттерны и фильтры
pre_text_pat   = re.compile(r"\[(\d{1,2}:\d{2}), (\d{1,2}\.\d{1,2}\.\d{4})] (.*?):")
date_in_msg    = re.compile(r'\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b')
filter_words   = ["попу","аор","тск","мир","восход","ао кропоткинское",
                  "колхоз прогресс","сп коломейцево","пу","отд"]

# Сбор и обработка
messages_data = []
filtered = 0

for msg in driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text")]'):
    # пропускаем цитаты
    if msg.find_elements(By.XPATH, './/div[contains(@data-testid, "quoted-message")]'):
        continue

    txt = msg.text.strip()
    if not txt:
        continue

    # фильтр по словам
    low = txt.lower()
    if not any(re.search(rf"\b{re.escape(w)}\b", low) for w in filter_words):
        continue

    pre = msg.get_attribute("data-pre-plain-text") or ""
    m = pre_text_pat.search(pre)
    if not m:
        continue

    time_str, date_str, sender = m.group(1), m.group(2), m.group(3)
    # очистка текста
    single = clean_text(" ".join(txt.splitlines()))

    # извлечение даты из текста
    dm = date_in_msg.search(single)
    if dm:
        message_date = dm.group(0)
        single = single.replace(message_date, "").strip()
    else:
        message_date = date_str[:-5]  # без года, например "17.04"

    # Собираем output_line для записи в файл
    output_line = f"{message_date} {single}"

    # Запись в message.txt
    try:
        with open('message.txt', 'a', encoding='utf-8') as f:
            f.write(f"{output_line}\n")
        print(f"{filtered+1}. Отправитель: {sender} | Дата: {date_str} {time_str} | Дата из сообщения: {message_date} | Сообщение: {single}")
    except Exception as e:
        print("Ошибка записи message.txt:", e)

    # Парсим datetime для Word
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    except:
        dt = datetime.now()

    filtered += 1
    messages_data.append({'sender': sender, 'text': single, 'datetime': dt})

# Сохраняем в Word
if messages_data:
    save_messages_to_word(messages_data)
else:
    print("Сообщения с заданными словами не найдены.")

driver.quit()
