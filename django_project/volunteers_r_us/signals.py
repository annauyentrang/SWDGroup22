from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Event, Match
from django.apps import apps

@receiver(post_save, sender=Event)
def on_event_created(sender, instance, created, **kwargs):
    if created:
        notify_candidates_for_event(instance)

@receiver(post_save, sender=Match)
def on_match_created(sender, instance, created, **kwargs):
    if created:
        create_match_notification(instance.volunteer, instance.event)

@receiver(m2m_changed, sender=Event.required_skills.through)
def on_event_skills_set(sender, instance, action, **kwargs):
    if action in {"post_add", "post_set"}:
        notify_candidates_for_event(instance)
