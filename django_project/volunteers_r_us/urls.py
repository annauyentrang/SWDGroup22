from django.urls import path
from . import views
from .views_matching import matching_page, assign_volunteer

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path("profile/", views.profile_form, name="profile_form"),
    path("events/", views.event_form, name="event_form"),
    path("volunteer_history/", views.volunteer_history, name="volunteer_history"),
    path("volunteer_history/<int:volunteer_id>/", views.volunteer_history, name="volunteer_history_by_id"),
    path("matching/", matching_page, name="match_volunteer"),
    path("matching/assign/", assign_volunteer, name="assign_volunteer"),
]
