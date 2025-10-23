from django.apps import apps

def create_match_notification(user, event):
    Notification = apps.get_model("notify", "Notification")
    Notification.objects.create(
        user=user,
        title=f"Matched to {event.name}",
        body=f"Starts {event.start_time}",
        url=f"https://your-host/events/{event.id}"
    )