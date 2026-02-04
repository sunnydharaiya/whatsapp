from django.core.management.base import BaseCommand
from django.utils import timezone
from whatsapp.models import Campaign, Contact
import time
import urllib.parse
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Command(BaseCommand):
    help = "TEST MODE: Send WhatsApp messages with 3s delay + live logs"

    def add_arguments(self, parser):
        parser.add_argument("campaign_id", type=int)

    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def handle(self, *args, **kwargs):
        self.log("Starting WhatsApp automation")

        os.makedirs(r"C:\wa_profile", exist_ok=True)

        campaign = Campaign.objects.get(id=kwargs["campaign_id"])
        self.log(f"Loaded campaign: {campaign.id}")

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument(r"--user-data-dir=C:\wa_profile")

        self.log("Launching Chrome with saved WhatsApp profile")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        self.log("Opening WhatsApp Web")
        driver.get("https://web.whatsapp.com")

        self.log("Waiting 25 seconds for QR / session restore")
        time.sleep(25)

        contacts = list(
            Contact.objects.filter(contactgroup__in=campaign.groups.all())
            .distinct()[: campaign.daily_limit]
        )
        self.log(f"Total contacts to send: {len(contacts)}")

        for index, contact in enumerate(contacts, start=1):
            try:
                self.log(f"[{index}] Preparing message for {contact.phone}")

                text = campaign.message.text.replace("{name}", contact.name)
                encoded_text = urllib.parse.quote(text)

                url = f"https://web.whatsapp.com/send?phone={contact.phone}&text={encoded_text}"
                driver.get(url)

                self.log("Waiting for chat to load (8s)")
                time.sleep(8)

                message_box = driver.find_element(
                    By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"
                )

                self.log("Sending message")
                message_box.send_keys(Keys.ENTER)

                self.log(f"✅ Sent successfully to {contact.phone}")

                self.log("Sleeping 3 seconds (TEST MODE)")
                time.sleep(3)

            except Exception as e:
                self.log(f"❌ FAILED for {contact.phone}")
                self.log(str(e))
                time.sleep(3)

        self.log("All messages processed")
        campaign.sent_today += len(contacts)
        campaign.last_run = timezone.now()
        campaign.save()
        self.log("Closing browser")
        driver.quit()
