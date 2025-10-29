from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Notification
from .models import VolunteerParticipation
from .models import Profile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")
    list_filter = ("created_at",)




# admin.py
from django.contrib import admin
from .models import Assignment

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id","volunteer_id","volunteer_name","event_id","event_title","status","notify","override","created_by","created_at")
    list_filter = ("status","notify","override","created_at")
    search_fields = ("volunteer_id","volunteer_name","event_id","event_title","match_reason","admin_notes")
    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "state", "zipcode", "updated_at")
    search_fields = ("user__email", "full_name", "city", "zipcode")


@admin.register(VolunteerParticipation)
class VolunteerParticipationAdmin(admin.ModelAdmin):
    list_display  = ("volunteer_name", "event_name", "event_date", "urgency", "status", "capacity_current", "capacity_total")
    list_filter   = ("urgency", "status", "event_date")
    search_fields = ("volunteer_name", "event_name", "location", "languages", "required_skills")

