# volunteers_r_us/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Skill, Event, VolunteerProfile, Match,
    Notification, Assignment, VolunteerParticipation, Profile
)

# ----- USER ADMIN -----
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )


# ----- OTHER MODELS -----
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "urgency", "event_date")
    list_filter = ("urgency", "event_date")
    search_fields = ("name", "location")


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__email",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("volunteer", "event", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("volunteer__email", "event__name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "message")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "volunteer", "event", "status",
        "notify", "override", "created_by", "created_at"
    )
    list_filter = ("status", "notify", "override", "created_at")
    search_fields = ("volunteer__email", "event__name", "match_reason", "admin_notes")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "state", "zipcode", "updated_at")
    search_fields = ("user__email", "full_name", "city", "zipcode")


@admin.register(VolunteerParticipation)
class VolunteerParticipationAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer_name", "event_name", "event_date",
        "urgency", "status", "capacity_current", "capacity_total"
    )
    list_filter = ("urgency", "status", "event_date")
    search_fields = (
        "volunteer_name", "event_name", "location",
        "languages", "required_skills"
    )

