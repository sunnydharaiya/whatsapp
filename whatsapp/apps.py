from django.apps import AppConfig


class WhatsappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp"

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.db.utils import OperationalError

        def run_ensure_contact_groups(sender, **kwargs):
            if sender.name == "whatsapp":
                from .services.contact_groups import ensure_contact_groups
                ensure_contact_groups()

        post_migrate.connect(run_ensure_contact_groups, sender=self)

        try:
            from .services.contact_groups import ensure_contact_groups
            ensure_contact_groups()
        except OperationalError:
            pass  # Tables not ready yet (e.g. during migrate)