# services/whatsapp_sender.py

import time, urllib.parse, os
from datetime import datetime
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from ..models import CampaignLog, CampaignRun, Contact


class WhatsAppSender:

    def __init__(self, campaign):
        self.campaign = campaign
        self._log_entry = None  # one log per run, all lines in one message

    def log(self, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n"
        if self._log_entry is None:
            self._log_entry = CampaignLog.objects.create(
                campaign=self.campaign,
                message=line
            )
        else:
            self._log_entry.message += line
            self._log_entry.save(update_fields=["message"])

    def run(self):
        self._run = CampaignRun.objects.create(campaign=self.campaign)
        self._log_entry = CampaignLog.objects.create(
            campaign=self.campaign,
            run=self._run,
            message="",
        )
        self.log("Starting WhatsApp automation")

        os.makedirs(r"C:\wa_profile", exist_ok=True)

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument(r"--user-data-dir=C:\wa_profile")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        self.log("Opening WhatsApp Web")
        driver.get("https://web.whatsapp.com")
        time.sleep(25)

        contacts = list(
            Contact.objects.filter(contactgroup__in=self.campaign.groups.all())
            .distinct()[: self.campaign.daily_limit]
        )
        self.log(f"Total contacts: {len(contacts)}")

        for i, contact in enumerate(contacts, 1):
            try:
                text = self.campaign.message.text.replace("{name}")
                encoded = urllib.parse.quote(text)
                url = f"https://web.whatsapp.com/send?phone={contact.phone}&text={encoded}"
                driver.get(url)

                time.sleep(8)

                box = driver.find_element(
                    By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"
                )
                box.send_keys(Keys.ENTER)

                self.log(f"✅ Sent to {contact.phone}")
                time.sleep(3)

            except Exception as e:
                self.log(f"❌ Failed for {contact.phone} → {e}")
                time.sleep(3)

        driver.quit()
        self._run.completed_at = timezone.now()
        self._run.sent_count = len(contacts)
        self._run.save()
        self.campaign.sent_today += len(contacts)
        self.campaign.last_run = timezone.now()
        self.campaign.save()
        self.log("Campaign completed")
