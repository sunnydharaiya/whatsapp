import time, random
from celery import shared_task
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

@shared_task
def send_whatsapp(numbers, message):
    options = Options()
    options.add_argument("--user-data-dir=./chrome-profile")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get("https://web.whatsapp.com")
    time.sleep(25)  # Scan QR once

    for phone in numbers:
        delay = random.randint(60, 140)
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
        driver.get(url)
        time.sleep(12)

        try:
            send_btn = driver.find_element(By.XPATH, "//span[@data-icon='send']")
            send_btn.click()
        except:
            pass

        time.sleep(delay)

    driver.quit()
