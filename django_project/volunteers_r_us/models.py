from django.db import models
from django.conf import settings
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
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

URGENCY = [("L","Low"),("M","Medium"),("H","High")]

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=200)
    required_skills = models.ManyToManyField(Skill, related_name="events")
    urgency = models.CharField(max_length=1, choices=URGENCY)
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name


class VolunteerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vol_profile")
    skills = models.ManyToManyField(Skill, related_name="volunteers", blank=True)
    def __str__(self): return f"{self.user}"

class Match(models.Model):
    PENDING, CONFIRMED, DECLINED = "P","C","D"
    STATUS_CHOICES = [(PENDING,"pending"),(CONFIRMED,"confirmed"),(DECLINED,"declined")]
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches")
    event     = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="matches")
    status    = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("volunteer","event")  # prevent duplicate matches
        indexes = [models.Index(fields=["volunteer","event"]), models.Index(fields=["status"])]

# ---------------------------
# Notification Model
# ---------------------------
class Notification(models.Model):
    # Keep nullable so migrations don't ask for a default for legacy NULL rows.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user} at {self.created_at}"




    






# ---------------------------
# Assignment Model
# ---------------------------

# models.py
from django.conf import settings
from django.db import models

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

    # Using raw ids/titles because you said you don't have Volunteer/Event models yet
    volunteer_id   = models.CharField(max_length=64)
    volunteer_name = models.CharField(max_length=255, blank=True)
    event_id       = models.CharField(max_length=64)
    event_title    = models.CharField(max_length=255, blank=True)

    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ASSIGNED)
    notify   = models.BooleanField(default=False)
    override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)
    admin_notes     = models.TextField(blank=True)

    match_score  = models.FloatField(default=0)
    match_reason = models.TextField(blank=True)
    warnings     = models.JSONField(default=list, blank=True)  # OK on Django 3.1+

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("volunteer_id", "event_id")
        indexes = [
            models.Index(fields=["event_id", "status"]),
            models.Index(fields=["volunteer_id"]),
        ]

    def __str__(self):
        return f"{self.volunteer_id} → {self.event_id} ({self.status})"

class VolunteerParticipation(models.Model):
    class Urgency(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    class Status(models.TextChoices):
        REGISTERED = "Registered", "Registered"
        ATTENDED = "Attended", "Attended"
        NO_SHOW = "No-Show", "No-Show"
        CANCELLED = "Cancelled", "Cancelled"

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

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=50)
    address1  = models.CharField(max_length=100)
    address2  = models.CharField(max_length=100, blank=True)
    city      = models.CharField(max_length=100)
    state     = models.CharField(max_length=2)
    zipcode   = models.CharField(max_length=10)
    skills        = models.JSONField(default=list)
    preferences   = models.TextField(blank=True)
    availability  = models.JSONField(default=list)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    # Store list of skill codes (e.g., ["FIRST_AID","CARPENTRY"])
    skills = models.JSONField(default=list)

    preferences = models.TextField(blank=True)

    # Store list of ISO dates (e.g., ["2025-11-02", "2025-11-09"])
    availability = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #def skill_labels(self):
        #label_map = dict(SKILL_CHOICES)
        #return [label_map.get(code, code) for code in self.skills]

    def __str__(self):
        return f"Profile<{self.user}>"

