from django.urls import path
from . import views

urlpatterns = [
    path("volunteers/", views.volunteers_api),
    path("events/", views.events_api),
    path("validate/volunteer/", views.validate_volunteer),
    path("validate/event/", views.validate_event),
    path("match/", views.match_api),
]