from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from .models import Campaign, Contact
from .tasks import send_whatsapp

def run_campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if campaign.sent_today >= campaign.daily_limit:
        return HttpResponse("Daily limit reached")

    contacts = Contact.objects.filter(contactgroup__in=campaign.groups.all()).distinct()[:campaign.daily_limit]
    numbers = [c.phone for c in contacts]

    send_whatsapp.delay(numbers, campaign.message.text)
    campaign.sent_today += len(numbers)
    campaign.last_run = timezone.now()
    campaign.save()

    return HttpResponse("Campaign started")
