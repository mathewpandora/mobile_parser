from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import time
from xml.etree import ElementTree as ET
from datetime import datetime
import re

desired_caps = {
    "platformName": "Android",
    "deviceName": "emulator-5554",
    # "app": "/Users/mathewpandora/Desktop/mobile_parser/app_xapk/ru.dewish.campus.apk",
    "automationName": "UiAutomator2",
    "udid": "emulator-5554",
    "appPackage": "ru.dewish.campus",
    "appActivity": "ru.campus.mobile.app.MainActivity",
    "appWaitActivity": "*",
    "autoGrantPermissions": True,
    "newCommandTimeout": 300,
    "adbExecTimeout": 200000,
    "uiautomator2ServerLaunchTimeout": 60000,
    "noReset": True,
    "dontStopAppOnReset": True
}

options = UiAutomator2Options().load_capabilities(desired_caps)

driver = webdriver.Remote(
    command_executor='http://127.0.0.1:4723/wd/hub',
    options=options
)

time.sleep(1.0)

try:
    el = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((AppiumBy.XPATH, "//*[contains(@text,'Отзывы на преподавател')]"))
    )
    r = el.rect
    x = int(r["x"] + r["width"] / 2)
    y = int(r["y"] + r["height"] / 2)
    try:
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
    except Exception:
        el.click()
except Exception:
    pass

time.sleep(1.0)
try:
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((AppiumBy.XPATH, "//*[@text='Reviews']"))
    )
except Exception:
    pass
try:
    WebDriverWait(driver, 15).until(
        EC.invisibility_of_element_located((AppiumBy.CLASS_NAME, "android.widget.ProgressBar"))
    )
except Exception:
    pass
time.sleep(0.5)

# Вытянуть все текстовые значения из XML-дерева (без тегов)
def extract_texts_from_xml(xml_string: str):
    texts = []
    try:
        root = ET.fromstring(xml_string)
        for node in root.iter():
            value = node.attrib.get("text")
            if value:
                value = value.strip()
                if value:
                    texts.append(value)
    except Exception:
        pass
    # сохраняем порядок, убираем дубликаты
    seen = set()
    unique_texts = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            unique_texts.append(t)
    return unique_texts

# Прокрутить страницу вверх до начала (остановиться, когда контент больше не меняется)
def scroll_to_top(driver, max_attempts: int = 6):
    last_hash = None
    stable_hits = 0
    for _ in range(max_attempts):
        xml = driver.page_source
        h = hash(xml)
        if h == last_hash:
            stable_hits += 1
            if stable_hits >= 2:
                break
        else:
            stable_hits = 0
        last_hash = h
        try:
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 50, "top": 300, "width": 980, "height": 1700, "direction": "up", "percent": 0.9}
            )
        except Exception:
            break
        time.sleep(0.2)

# Собрать все тексты, пролистывая страницу вниз до конца
def collect_texts_scrolling(driver, max_attempts: int = 30):
    all_texts = []
    seen = set()
    last_hash = None
    stable_hits = 0
    for _ in range(max_attempts):
        xml = driver.page_source
        # собрать тексты текущего экрана
        for t in extract_texts_from_xml(xml):
            if t not in seen:
                seen.add(t)
                all_texts.append(t)
        # проверка на застой контента
        h = hash(xml)
        if h == last_hash:
            stable_hits += 1
            if stable_hits >= 2:
                break
        else:
            stable_hits = 0
        last_hash = h
        # скролл вниз
        try:
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 50, "top": 300, "width": 980, "height": 1700, "direction": "down", "percent": 0.9}
            )
        except Exception:
            break
        time.sleep(0.15)
    return all_texts

def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

def sanitize_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_", "."))
    safe = safe.strip().replace(" ", "_")
    if not safe:
        safe = f"teacher_{int(time.time())}"
    return safe[:120]

def click_show_more_all(driver, max_passes: int = 8, scroll_tries: int = 3):
    last_xml = None
    for _ in range(max_passes):
        try:
            buttons = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView[@clickable='true' and @text='Show more']")
            if not buttons:
                buttons = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView[contains(@text,'Show more')]")
        except Exception:
            buttons = []
        if not buttons:
            xml = driver.page_source
            if xml == last_xml:
                break
            need_scroll = "Show more" in xml
            if not need_scroll:
                break
            scrolled = False
            for _ in range(scroll_tries):
                try:
                    driver.execute_script(
                        "mobile: scrollGesture",
                        {"left": 50, "top": 900, "width": 980, "height": 1000, "direction": "down", "percent": 0.7}
                    )
                    scrolled = True
                    time.sleep(0.2)
                    buttons = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView[contains(@text,'Show more')]")
                    if buttons:
                        break
                except Exception:
                    break
            if not scrolled:
                break
        clicked = False
        for b in buttons:
            try:
                r = b.rect
                cx = int(r["x"] + r["width"] / 2)
                cy = int(r["y"] + r["height"] / 2)
                try:
                    driver.execute_script("mobile: clickGesture", {"x": cx, "y": cy})
                except Exception:
                    try:
                        b.click()
                    except Exception:
                        continue
                clicked = True
                time.sleep(0.25)
            except Exception:
                continue
        xml = driver.page_source
        if xml == last_xml and not clicked:
            break
        last_xml = xml

def save_teacher_dom(teacher_name: str, dom_content: str):
    return

month_year_re = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}$")
rating_re = re.compile(r"^\d{1,2}(?:\.\d)?$")

def extract_texts_in_order(xml_string: str):
    texts = []
    try:
        root = ET.fromstring(xml_string)
        for node in root.iter():
            t = node.attrib.get("text")
            if t:
                t = t.strip()
                if t:
                    texts.append(t)
    except Exception:
        pass
    return texts

def parse_reviews_from_xml(xml_string: str):
    texts = extract_texts_in_order(xml_string)
    reviews = []
    i = 0
    n = len(texts)
    while i < n:
        t = texts[i]
        if month_year_re.match(t):
            date = t
            author = ""
            for j in range(max(0, i-3), i):
                cand = texts[j]
                if cand.lower() in ("reviews", "rules", "characteristics", "rate teacher", "show more"):
                    continue
                if rating_re.match(cand):
                    continue
                author = cand
            rating = ""
            for k in range(i, min(n, i+8)):
                cand = texts[k]
                if rating_re.match(cand):
                    rating = cand
                    break
            tags = []
            text = ""
            for k in range(i+1, min(n, i+30)):
                cand = texts[k]
                if month_year_re.match(cand):
                    break
                if not text:
                    if len(cand) <= 24 or cand.startswith("+ ") or cand.endswith("%)") or cand in ("Anonymous",):
                        tags.append(cand)
                        continue
                    if cand.lower() in ("reviews", "rules", "characteristics", "rate teacher", "show more"):
                        continue
                    text = cand
                else:
                    if len(text) < 400 and len(cand) > 10 and not month_year_re.match(cand):
                        text += " " + cand
            reviews.append({
                "author": author or "Anonymous",
                "date": date,
                "rating": rating,
                "tags": tags,
                "text": text
            })
        i += 1
    return reviews

def collect_all_reviews_scrolling(driver, max_attempts: int = 60):
    all_reviews = []
    seen_keys = set()
    last_hash = None
    stable = 0
    # начинаем с прокрутки к началу списка отзывов
    try:
        scroll_to_top(driver, max_attempts=8)
    except Exception:
        pass
    for _ in range(max_attempts):
        xml = driver.page_source
        parsed = parse_reviews_from_xml(xml)
        for r in parsed:
            key = (r.get("date", ""), (r.get("text", "") or "")[:80])
            if key not in seen_keys:
                seen_keys.add(key)
                all_reviews.append(r)
        h = hash(xml)
        if h == last_hash:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last_hash = h
        try:
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 50, "top": 900, "width": 980, "height": 1000, "direction": "down", "percent": 0.92}
            )
        except Exception:
            break
        time.sleep(0.22)
    return all_reviews

def parse_total_rating(texts):
    total = ""
    # Ищем общий рейтинг - большое число в начале страницы
    for i, t in enumerate(texts[:50]):  # Ищем в первых 50 элементах
        if re.match(r"^(\d(?:\.\d)?)$", t):
            # Проверяем, что это не рейтинг отзыва (не рядом с датой)
            is_review_rating = False
            for j in range(max(0, i-3), min(len(texts), i+3)):
                if month_year_re.match(texts[j]):
                    is_review_rating = True
                    break
            if not is_review_rating:
                total = t
                break
    return total

def parse_metrics(texts):
    metrics = []
    
    # Ищем блок метрик после "Rating was based on"
    start_idx = -1
    for i, text in enumerate(texts):
        if "Rating was based on" in text:
            start_idx = i + 1
            break
    
    if start_idx == -1:
        return metrics
    
    # Ищем метрики в блоке до "Characteristics"
    end_idx = len(texts)
    for i in range(start_idx, len(texts)):
        if texts[i] == "Characteristics":
            end_idx = i
            break
    
    for i in range(start_idx, end_idx):
        text = texts[i]
        if re.match(r"^(\d(?:\.\d)?)$", text) and i > 0:
            # Это числовой рейтинг, ищем название метрики перед ним
            metric_name = texts[i-1] if i-1 < len(texts) else ""
            if len(metric_name) > 3 and not re.match(r"^(\d(?:\.\d)?)$", metric_name):
                metrics.append((metric_name, text))
    
    return metrics

def parse_characteristics(texts):
    chars = []
    
    # Ищем блок характеристик после "Characteristics"
    start_idx = -1
    for i, text in enumerate(texts):
        if text == "Characteristics":
            start_idx = i + 1
            break
    
    if start_idx == -1:
        return chars
    
    # Ищем характеристики в блоке до "Reviews" или до конца
    end_idx = len(texts)
    for i in range(start_idx, len(texts)):
        if texts[i] == "Reviews":
            end_idx = i
            break
    
    for i in range(start_idx, end_idx):
        text = texts[i]
        # Ищем характеристики в формате "Название (XX%)"
        if "(" in text and "%)" in text:
            chars.append(text)
    
    return chars

def build_teacher_xml(name, xml_string, reviews):
    texts = extract_texts_in_order(xml_string)
    total = parse_total_rating(texts)
    metrics = parse_metrics(texts)
    chars = parse_characteristics(texts)
    root = ET.Element("teacher")
    root.set("name", name)
    info = ET.SubElement(root, "info")
    ET.SubElement(info, "total_rating").text = total
    ET.SubElement(info, "export_date").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ET.SubElement(info, "reviews_count").text = str(len(reviews))
    metrics_el = ET.SubElement(root, "metrics")
    for label, val in metrics:
        m = ET.SubElement(metrics_el, "metric")
        ET.SubElement(m, "name").text = label
        ET.SubElement(m, "value").text = val
    chars_el = ET.SubElement(root, "characteristics")
    for c in chars:
        char_el = ET.SubElement(chars_el, "characteristic")
        # Парсим название и процент из строки вида "Название (XX%)"
        if "(" in c and "%)" in c:
            name_part = c.split("(")[0].strip()
            percent_part = c.split("(")[1].replace("%)", "").strip()
            ET.SubElement(char_el, "name").text = name_part
            ET.SubElement(char_el, "value").text = percent_part
        else:
            ET.SubElement(char_el, "name").text = c
            ET.SubElement(char_el, "value").text = ""
    revs_el = ET.SubElement(root, "reviews")
    for r in reviews:
        re_el = ET.SubElement(revs_el, "review")
        ET.SubElement(re_el, "author").text = r.get("author", "")
        ET.SubElement(re_el, "date").text = r.get("date", "")
        ET.SubElement(re_el, "rating").text = r.get("rating", "")
        # теги не сохраняем в XML
        if False and r.get("tags"):
            tags_el = ET.SubElement(re_el, "tags")
            for tag in r.get("tags", []):
                ET.SubElement(tags_el, "tag").text = tag
        ET.SubElement(re_el, "text").text = r.get("text", "")
    # Форматируем XML с отступами
    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                indent(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

def save_teacher_xml(teacher_name: str, xml_string: str):
    try:
        safe_name = sanitize_filename(teacher_name)
        filename = f"outputs/{safe_name}.xml"
        ensure_dir("outputs")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(xml_string)
        print(f"💾 XML сохранен: {filename}", flush=True)
    except Exception as e:
        print(f"❌ Ошибка сохранения XML для {teacher_name}: {e}", flush=True)

def print_teacher_info(name, total, metrics, chars, reviews, dom_content=""):
    pass

visited = set()
items_cache = []
cache_valid = False
main_page_start_time = time.time()

while True:
    # Дожидаемся заголовка Teachers и каждый цикл печатаем актуальное дерево списка
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//*[@text='Teachers']"))
        )
    except Exception:
        time.sleep(0.3)
    # Убрали вывод DOM главной страницы для ускорения

    # Используем кэш элементов если он валиден, иначе обновляем
    if not cache_valid:
        # Кардинально новый подход - ищем только в определенной области экрана
        screen_height = driver.get_window_size()['height']
        
        # Супер быстрый поиск - ищем только видимые элементы
        items = []
        
        # СУПЕР БЫСТРЫЙ поиск - ищем только в определенной области экрана
        # Ограничиваем поиск только видимой областью (первые 1500px)
        all_views = driver.find_elements(
            AppiumBy.XPATH, 
            "//android.view.View[@clickable='true' and @bounds]"
        )
        
        seen_bounds = set()  # Для избежания дубликатов
        
        for view in all_views:
            try:
                rect = view.rect
                # СТРОГО ограничиваем поиск только видимой областью
                if rect['y'] < 1500 and rect['y'] > 0 and rect['height'] > 50:
                    # Быстрая проверка на рейтинг
                    rating_texts = view.find_elements(AppiumBy.XPATH, ".//android.widget.TextView[contains(@text,' rating')]")
                    if rating_texts:
                        # Создаем уникальный ключ для избежания дубликатов
                        bounds_key = f"{rect['x']},{rect['y']}"
                        if bounds_key not in seen_bounds:
                            seen_bounds.add(bounds_key)
                            items.append(view)
            except:
                continue
        
        items_cache = items
        cache_valid = True
    else:
        items = items_cache

    progressed = False
    refresh_needed = False
    
    if len(items) == 0:
        cache_valid = False
        continue
    
    for it in items:
        try:
            # Более быстрый поиск имени - ищем первый TextView с текстом
            text_views = it.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
            name = ""
            name_el = None
            for tv in text_views:
                text = tv.get_attribute("text") or ""
                if text and len(text) > 10 and " rating" not in text and not text.isdigit():  # Имя длиннее 10 символов, не рейтинг и не число
                    name = text
                    name_el = tv
                    break
        except Exception:
            name = ""
        
        if not name:
            # без имени пропускаем молча
            continue
            
        safe_name = sanitize_filename(name)
        out_path = os.path.join("outputs", f"{safe_name}.xml")
        if os.path.exists(out_path):
            print(f"СКИП: {name}", flush=True)
            visited.add(name)
            continue
        if name in visited:
            # уже посещенного пропускаем молча
            continue
        ir = it.rect
        icx = int(ir["x"] + ir["width"] / 2)
        icy = int(ir["y"] + ir["height"] / 2)
        try:
            driver.execute_script("mobile: clickGesture", {"x": icx, "y": icy})
        except Exception as e1:
            try:
                it.click()
            except Exception as e2:
                try:
                    nr = name_el.rect
                    nx = int(nr["x"] + nr["width"] / 2)
                    ny = int(nr["y"] + nr["height"] / 2)
                    driver.execute_script("mobile: clickGesture", {"x": nx, "y": ny})
                except Exception as e3:
                    continue
        visited.add(name)
        progressed = True
        
        current_time = time.time()
        
        try:
            WebDriverWait(driver, 3).until(EC.staleness_of(name_el))
        except Exception:
            time.sleep(0.3)
        
        print(f"ОБРАБОТКА: {name}", flush=True)
        try:
            click_show_more_all(driver)
        except Exception:
            pass
        
        # Парсим метрики и характеристики СРАЗУ после Show more, до скроллинга
        dom_after_show_more = driver.page_source
        texts_after_show_more = extract_texts_in_order(dom_after_show_more)
        total = parse_total_rating(texts_after_show_more)
        metrics = parse_metrics(texts_after_show_more)
        chars = parse_characteristics(texts_after_show_more)
        
        # вывод отключен
        
        # Теперь скроллим и собираем отзывы
        reviews = collect_all_reviews_scrolling(driver)
        
        save_teacher_dom(name, dom_after_show_more)
        try:
            print_teacher_info(name, total, metrics, chars, reviews, driver.page_source)
            teacher_xml = build_teacher_xml(name, dom_after_show_more, reviews)
            save_teacher_xml(name, teacher_xml)
        except Exception as e:
            print(f"❌ Ошибка генерации XML для {name}: {e}", flush=True)
        
        # Логируем время обработки карточки
        card_end_time = time.time()
        card_processing_time = card_end_time - current_time
        # вывод времени отключен
        
        try:
            driver.back()
        except Exception:
            pass
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((AppiumBy.XPATH, "//*[@text='Teachers']"))
            )
        except Exception:
            time.sleep(0.1)
        # Убрали вывод DOM после возврата для ускорения
        time.sleep(0.1)
        # После возврата обновим коллекцию элементов на следующей итерации
        cache_valid = False
        # Сбрасываем время начала главной страницы
        main_page_start_time = time.time()
        break
    if not progressed:
        # Сбрасываем время при скролле
        main_page_start_time = time.time()
        try:
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 50, "top": 350, "width": 980, "height": 1650, "direction": "down", "percent": 0.85}
            )
            # После скролла ждем немного для стабилизации DOM
            time.sleep(0.3)
            # ОБЯЗАТЕЛЬНО обновляем кэш после скролла
            cache_valid = False
            # лог скролла отключен
        except Exception:
            break

if os.environ.get("PARSE_ONCE") == "1":
    driver.quit()
    sys.exit(0)
# Бесконечный цикл - скрипт работает постоянно
while True:
    time.sleep(60)  # Пауза 1 минута между циклами


