# volunteers_r_us/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# ---------------------------
# Custom User Model
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150, blank=True)
    last_name  = models.CharField(max_length=150, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# ---------------------------
# Core Domain
# ---------------------------
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name


class Event(models.Model):
    class Urgency(models.TextChoices):
        LOW    = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH   = "high", "High"

    name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=255)
    required_skills = models.ManyToManyField(Skill, related_name="events", blank=True)
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name


class VolunteerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vol_profile")
    skills = models.ManyToManyField(Skill, related_name="volunteers", blank=True)
    def __str__(self): return f"{self.user}"


class Match(models.Model):
    PENDING, CONFIRMED, DECLINED = "P", "C", "D"
    STATUS_CHOICES = [(PENDING, "pending"), (CONFIRMED, "confirmed"), (DECLINED, "declined")]

    volunteer  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches")
    event = models.ForeignKey("Event", on_delete=models.CASCADE, null=True, blank=True)
    status     = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["volunteer", "event"], name="uq_match_volunteer_event")
        ]
        indexes = [
            models.Index(fields=["volunteer", "event"]),
            models.Index(fields=["status"]),
        ]

# ---------------------------
# Assignment (now using FKs)
# ---------------------------
class Assignment(models.Model):
    ASSIGNED  = "assigned"
    ATTENDED  = "attended"
    NO_SHOW   = "no_show"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (ASSIGNED,  "Assigned"),
        (ATTENDED,  "Attended"),
        (NO_SHOW,   "No-Show"),
        (CANCELLED, "Cancelled"),
    ]

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="assignments"
    )
    event = models.ForeignKey(
        "Event", null=True, blank=True, on_delete=models.CASCADE, related_name="assignments"
    )

    # optional denormalized display fields
    volunteer_name = models.CharField(max_length=255, blank=True)
    event_title    = models.CharField(max_length=255, blank=True)

    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ASSIGNED)
    notify   = models.BooleanField(default=False)
    override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)
    admin_notes     = models.TextField(blank=True)

    match_score  = models.FloatField(default=0)
    match_reason = models.TextField(blank=True)
    warnings     = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_assignments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["volunteer", "event"], name="uq_assignment_volunteer_event")
        ]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["volunteer"]),
        ]

    def __str__(self):
        return f"{self.volunteer} → {self.event} ({self.status})"


# ---------------------------
# Reporting/Denormalized Table
# ---------------------------
class VolunteerParticipation(models.Model):
    class Urgency(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    class Status(models.TextChoices):
        REGISTERED = "Registered", "Registered"
        ATTENDED   = "Attended", "Attended"
        NO_SHOW    = "No-Show", "No-Show"
        CANCELLED  = "Cancelled", "Cancelled"

    volunteer_name   = models.CharField(max_length=100)
    event_name       = models.CharField(max_length=120)
    description      = models.TextField(blank=True, default="—")
    location         = models.CharField(max_length=160)
    required_skills  = models.CharField(max_length=160, help_text="Comma-separated (e.g., Cooking,Organization)")
    urgency          = models.CharField(max_length=6, choices=Urgency.choices)
    event_date       = models.DateField()
    capacity_current = models.PositiveIntegerField(default=0)
    capacity_total   = models.PositiveIntegerField()
    languages        = models.CharField(max_length=160, help_text="Comma-separated (e.g., English,Spanish)")
    status           = models.CharField(max_length=10, choices=Status.choices)

    class Meta:
        db_table = "volunteer_participation"
        ordering = ["event_date", "volunteer_name"]

    def __str__(self):
        return f"{self.volunteer_name} – {self.event_name} ({self.event_date})"


# ---------------------------
# User Profile
# ---------------------------
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=50)
    address1  = models.CharField(max_length=100)
    address2  = models.CharField(max_length=100, blank=True)
    city      = models.CharField(max_length=100)
    state     = models.CharField(max_length=2)
    zipcode   = models.CharField(max_length=10)

    # lists like ["FIRST_AID","CARPENTRY"] and ["2025-11-02","2025-11-09"]
    skills       = models.JSONField(default=list)
    preferences  = models.TextField(blank=True)
    availability = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user}>"
