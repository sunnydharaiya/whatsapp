from django.contrib import admin
from .models import Contact, ContactGroup, MessageTemplate, Campaign, ContactUpload, CampaignRun, CampaignLog
from .services.whatsapp_sender import WhatsAppSender


@admin.action(description="▶ Send WhatsApp Campaign")
def send_campaign(modeladmin, request, queryset):
    for campaign in queryset:
        WhatsAppSender(campaign).run()


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "daily_limit", "sent_today", "last_run")
    actions = [send_campaign]

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "phone")

    def view_on_site(self, obj):
        return False


@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_count", "size")
    search_fields = ("name",)
    filter_horizontal = ("contacts",)

    def contact_count(self, obj):
        return obj.contacts.count()
    contact_count.short_description = "Total Contacts"


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("text", "image")


@admin.register(ContactUpload)
class ContactUploadAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at")
    search_fields = ("file",)
    readonly_fields = ("uploaded_at",)
    ordering = ("-uploaded_at",)


class CampaignLogInline(admin.StackedInline):
    model = CampaignLog
    fk_name = "run"
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ("campaign", "message", "created_at")
    fields = ("campaign", "created_at", "message")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CampaignRun)
class CampaignRunAdmin(admin.ModelAdmin):
    list_display = ("campaign", "started_at", "completed_at", "sent_count")
    list_filter = ("campaign", "started_at")
    search_fields = ("campaign__name",)
    readonly_fields = ("campaign", "started_at", "completed_at", "sent_count")
    ordering = ("-started_at",)
    inlines = [CampaignLogInline]


@admin.register(CampaignLog)
class CampaignLogAdmin(admin.ModelAdmin):
    list_display = ("campaign", "run", "message_preview", "created_at")
    list_filter = ("campaign", "run", "created_at")
    search_fields = ("message",)
    readonly_fields = ("campaign", "run", "message", "created_at")
    ordering = ("-created_at",)

    def message_preview(self, obj):
        return (obj.message[:80] + "…") if obj.message and len(obj.message) > 80 else (obj.message or "")
    message_preview.short_description = "Log"
