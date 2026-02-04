# whatsapp/services/contact_groups.py

from django.db import transaction
from whatsapp.models import Contact, ContactGroup

GROUP_SIZE = 100


def ensure_contact_groups():
    """Create groups of 100 contacts. Adds new groups for contacts not yet in any group."""
    all_contacts = list(Contact.objects.all().order_by("id"))

    if not all_contacts:
        return

    with transaction.atomic():
        if not ContactGroup.objects.exists():
            # No groups yet: create groups for all contacts in batches of 100
            for i in range(0, len(all_contacts), GROUP_SIZE):
                batch = all_contacts[i : i + GROUP_SIZE]
                group = ContactGroup.objects.create(
                    name=f"Group {(i // GROUP_SIZE) + 1}",
                    size=GROUP_SIZE,
                )
                group.contacts.add(*batch)
            return

        # Groups exist: find contacts not in any group and add new groups for them
        contacts_in_groups = set()
        for g in ContactGroup.objects.prefetch_related("contacts"):
            contacts_in_groups.update(c.id for c in g.contacts.all())

        unassigned = [c for c in all_contacts if c.id not in contacts_in_groups]
        if not unassigned:
            return

        base = ContactGroup.objects.count()
        for i in range(0, len(unassigned), GROUP_SIZE):
            batch = unassigned[i : i + GROUP_SIZE]
            group = ContactGroup.objects.create(
                name=f"Group {base + (i // GROUP_SIZE) + 1}",
                size=GROUP_SIZE,
            )
            group.contacts.add(*batch)
