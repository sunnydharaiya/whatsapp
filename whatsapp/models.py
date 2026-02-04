from django.db import models
from django.utils.html import format_html
from django.urls import reverse

class Contact(models.Model):
    phone = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.phone

    def get_absolute_url(self):
        return reverse("contact-detail", kwargs={"pk": self.pk})


class ContactGroup(models.Model):
    name = models.CharField(max_length=100)
    contacts = models.ManyToManyField(Contact)
    size = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.name


class MessageTemplate(models.Model):
    text = models.TextField()
    image = models.ImageField(
        upload_to="whatsapp_images/",
        blank=True,
        null=True
    )


    def __str__(self):
        return self.text[:40]


class Campaign(models.Model):
    name = models.CharField(max_length=100)
    message = models.ForeignKey(MessageTemplate, on_delete=models.CASCADE)
    groups = models.ManyToManyField(ContactGroup)
    daily_limit = models.PositiveIntegerField(default=100)
    sent_today = models.PositiveIntegerField(default=0)
    last_run = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class ContactUpload(models.Model):
    file = models.FileField(upload_to="contact_uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            self.process_file()

    def process_file(self):
        import openpyxl
        from .models import Contact

        wb = openpyxl.load_workbook(self.file.path)
        sheet = wb.active

        headers = {}
        for idx, cell in enumerate(sheet[1]):
            if cell.value:
                headers[str(cell.value).strip().lower()] = idx

        if 'phone' not in headers:
            return

        for row in sheet.iter_rows(min_row=2, values_only=True):
            phone = row[headers['phone']]
            if not phone:
                continue

            phone = str(phone).strip()

            Contact.objects.get_or_create(
                phone=phone,
            )



class CampaignRun(models.Model):
    """One row per campaign execution: when it ran and how many sent."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.campaign.name} @ {self.started_at}"


class CampaignLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="logs")
    run = models.ForeignKey(
        CampaignRun,
        on_delete=models.CASCADE,
        related_name="log",
        null=True,
        blank=True,
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign.name} - {self.created_at}"