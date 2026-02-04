# utils.py (or management command)

from .models import Contact, ContactGroup

def auto_create_groups(group_size=100):
    contacts = list(Contact.objects.all().order_by("id"))
    total = len(contacts)
    total_groups = math.ceil(total / group_size)

    for i in range(total_groups):
        start = i * group_size
        end = start + group_size
        chunk = contacts[start:end]

        group = ContactGroup.objects.create(
            name=f"Group {i + 1}",
            size=group_size
        )
        group.contacts.add(*chunk)
