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


