from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path("match/", views.match_volunteer, name="match_volunteer"),
    path("profile/", views.profile_form, name="profile_form"),
    path("events/", views.event_form, name="event_form"),
    path("match/", views.match_volunteer, name="match_volunteer"),
    path("volunteer_history/", views.volunteer_history, name="volunteer_history"),
    path("volunteer_history/<int:volunteer_id>/", views.volunteer_history, name="volunteer_history_by_id"),
]
