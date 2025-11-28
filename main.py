from appium import webdriver
from appium.options.android import UiAutomator2Options
import os
import sys
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

desired_caps = {
    "platformName": "Android",
    "deviceName": "emulator-5554",
    "app": "/Users/mathewpandora/Desktop/mobile_parser/app_xapk/ru.dewish.campus.apk",
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

print(driver.page_source)
clicked = False
for _ in range(15):
    try:
        el = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//*[@text='Москва']"))
        )
        el.click()
        clicked = True
        break
    except Exception:
        try:
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 50, "top": 250, "width": 980, "height": 1750, "direction": "down", "percent": 0.9}
            )
        except Exception:
            break

if clicked:
    time.sleep(1.5)
    variants = [
        "РЭУ им. Г.В. Плеханова",
        "РЭУ им.",
        "Плеханова",
        "РЭУ"
    ]
    xpath_union = " | ".join([f"//*[@text='{v}']" for v in variants] + [f"//*[contains(@text,'{v}')]" for v in variants])
    for _ in range(40):
        try:
            el2 = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_union))
            )
            el2.click()
            break
        except Exception:
            try:
                driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().textContains("РЭУ"))'
                )
            except Exception:
                try:
                    driver.execute_script(
                        "mobile: scrollGesture",
                        {"left": 50, "top": 250, "width": 980, "height": 1750, "direction": "down", "percent": 0.9}
                    )
                except Exception:
                    break

    time.sleep(1.5)
    btn_variants = [
        "Отзывы на преподавателей",
        "Отзывы о преподавателях",
        "Отзывы",
        "Отзывы на препоадавателей"
    ]
    btn_xpath = " | ".join([f"//*[@text='{v}']" for v in btn_variants] + [f"//*[contains(@text,'{v}')]" for v in btn_variants])
    for _ in range(40):
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((AppiumBy.XPATH, btn_xpath))
            )
            btn.click()
            break
        except Exception:
            try:
                driver.execute_script(
                    "mobile: scrollGesture",
                    {"left": 50, "top": 250, "width": 980, "height": 1750, "direction": "down", "percent": 0.9}
                )
            except Exception:
                break
if os.environ.get("PARSE_ONCE") == "1":
    driver.quit()
    sys.exit(0)
time.sleep(3600)
