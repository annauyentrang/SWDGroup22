# volunteers_r_us/signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Event, Match  # ensure Match is in this app's models

@receiver(post_save, sender=Event)
def on_event_saved(sender, instance, created, **kwargs):
    if created:                      # <- guard
        from .matching.notifications import notify_candidates_for_event
        notify_candidates_for_event(instance)

@receiver(post_save, sender=Match)
def on_match_created(sender, instance, created, **kwargs):
    if created:
        from .matching.notifications import create_match_notification
        create_match_notification(instance.volunteer, instance.event)

@receiver(m2m_changed, sender=Event.required_skills.through)
def on_event_skills_set(sender, instance, action, **kwargs):
    if action in {"post_add", "post_set", "post_remove"}:
        from .matching.notifications import notify_candidates_for_event
        notify_candidates_for_event(instance)
