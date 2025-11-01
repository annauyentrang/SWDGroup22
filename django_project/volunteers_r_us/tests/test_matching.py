# volunteers_r_us/tests/test_matching.py
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

from volunteers_r_us.models import VolunteerProfile, Assignment, Event, Skill
from notify.models import Notification


class MatchingFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()

        # org/staff user who operates the matching UI
        self.org = User.objects.create_user(email="org@example.com", password="pw")
        # volunteer user (linked to VolunteerProfile)
        self.vol = User.objects.create_user(email="vol@example.com", password="pw")

        # minimal volunteer profile
        self.vprof = VolunteerProfile.objects.create(user=self.vol)

        # event + skill (if your Event uses required_skills)
        self.skill = Skill.objects.create(name="First Aid / CPR")
        self.event = Event.objects.create(
            name="Clinic Day",
            description="Vitals",
            location="City Hall",
            urgency="high",
            event_date=date.today() + timedelta(days=7),
        )
        # if Event has m2m required_skills; if not, this no-ops
        try:
            self.event.required_skills.add(self.skill)
        except Exception:
            pass

    # ---------- GET page ----------

    def test_matching_page_requires_login(self):
        r = self.client.get(reverse("match_volunteer"))
        # default login URL name is "login" in your app; adapt if needed
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r["Location"])

    def test_matching_page_lists_volunteers_and_events(self):
        self.client.login(email="org@example.com", password="pw")
        r = self.client.get(reverse("match_volunteer"))
        self.assertEqual(r.status_code, 200)
        # page renders both lists
        self.assertContains(r, "Volunteer Matching")
        self.assertContains(r, "Clinic Day")
        self.assertContains(r, "vol@example.com")

    # ---------- POST assign ----------

    def test_assign_creates_assignment_and_notification_and_email(self):
        self.client.login(email="org@example.com", password="pw")

        # Simulate the selection made in the GET form (Profile.id + Event.id)
        # Your form posts volunteer_id=VolunteerProfile.id and event_id=Event.id
        payload = {
            "volunteer_id": self.vprof.id,
            "event_id": self.event.id,
        }
        r = self.client.post(reverse("assign_volunteer"), payload, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "assigned and notified")

        # Assignment persisted (volunteer is AUTH_USER, not profile)
        self.assertTrue(
            Assignment.objects.filter(volunteer=self.vol, event=self.event).exists()
        )
        a = Assignment.objects.get(volunteer=self.vol, event=self.event)
        self.assertEqual(a.status, Assignment.ASSIGNED)

        # Notification row created for the volunteer's user
        self.assertTrue(Notification.objects.filter(user=self.vol).exists())
        note = Notification.objects.filter(user=self.vol).latest("id")
        self.assertIn(self.event.name, note.title)

        # Email sent (locmem backend in tests)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.event.name, mail.outbox[0].subject)
        self.assertIn("vol@example.com", mail.outbox[0].to)

    def test_assign_is_idempotent_for_same_volunteer_and_event(self):
        self.client.login(email="org@example.com", password="pw")

        payload = {"volunteer_id": self.vprof.id, "event_id": self.event.id}
        # First POST
        self.client.post(reverse("assign_volunteer"), payload, follow=True)
        # Second POST should not create a duplicate row
        self.client.post(reverse("assign_volunteer"), payload, follow=True)

        self.assertEqual(
            Assignment.objects.filter(volunteer=self.vol, event=self.event).count(), 1
        )

    def test_assign_redirects_on_get(self):
        self.client.login(email="org@example.com", password="pw")
        r = self.client.get(reverse("assign_volunteer"))
        self.assertEqual(r.status_code, 302)  # view should redirect back to matching page
        self.assertIn(reverse("match_volunteer"), r["Location"])
