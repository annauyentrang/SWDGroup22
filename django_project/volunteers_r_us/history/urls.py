from django.urls import path
from . import views

app_name = "history"

urlpatterns = [
    path("volunteer-history/", views.volunteer_history, name="volunteer_history"),
    
]

