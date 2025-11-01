from django.contrib import admin
from notify.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id","user_email","title","is_read","created_at")

    @admin.display(ordering="user__email", description="User")
    def user_email(self, obj):
        u = obj.user
        return getattr(u, "email", u.id)
