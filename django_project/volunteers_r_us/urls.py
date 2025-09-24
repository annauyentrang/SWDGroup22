from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path("login/", views.login, name='login'),
    path("register/", views.register, name='register'),
    path("match/", views.match_volunteer, name="match_volunteer")

]
