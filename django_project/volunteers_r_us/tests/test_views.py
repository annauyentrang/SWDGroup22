import json
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from volunteers_r_us.models import VolunteerParticipation as VP, Assignment

User = get_user_model()


class MainViewsTests(TestCase):
    def setUp(self):
        # a user to exercise login_required views
        self.email = "ada@example.com"
        self.password = "Str0ngPa$$w0rd!"
        self.user = User.objects.create_user(email=self.email, password=self.password)

    # ---------- helpers ----------
    def _client_login(self):
        # client.login expects the model's USERNAME_FIELD
        username_field = User.USERNAME_FIELD
        return self.client.login(**{username_field: self.email, "password": self.password})

    # ---------- public / auth views ----------
    def test_home_renders(self):
        url = reverse("home")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_register_valid_then_login_success(self):
        # register
        url = reverse("register")
        payload = {
            "email": "newuser@example.com",
            "password": "B3tterPa$$word!",
            "confirm": "B3tterPa$$word!",
        }
        resp = self.client.post(url, data=payload, follow=False)
        # should redirect to login on success
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

        # login with new account
        login_resp = self.client.post(
            reverse("login"),
            data={"email": payload["email"], "password": payload["password"]},
            follow=False,
        )
        self.assertEqual(login_resp.status_code, 302)
        self.assertIn(reverse("home"), login_resp["Location"])

    def test_register_duplicate_email_shows_error(self):
        url = reverse("register")
        payload = {"email": self.email, "password": self.password, "confirm": self.password}
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"already exists", resp.content)

    def test_login_missing_fields_validation(self):
        resp = self.client.post(reverse("login"), data={"email": "", "password": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Email is required", resp.content)
        self.assertIn(b"Password is required", resp.content)

    def test_login_invalid_credentials(self):
        resp = self.client.post(reverse("login"), data={"email": self.email, "password": "nope"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password", resp.content)

    def test_logout_redirects_home(self):
        self._client_login()
        resp = self.client.get(reverse("logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("home"), resp["Location"])

    # ---------- login_required: profile_form ----------
    def test_profile_form_requires_login_then_renders(self):
        # redirect to login when anonymous
        resp_anon = self.client.get(reverse("profile_form"))
        self.assertEqual(resp_anon.status_code, 302)

        # logged-in can view
        self._client_login()
        resp = self.client.get(reverse("profile_form"))
        self.assertEqual(resp.status_code, 200)
        # context contains form and choice lists
        self.assertIn("form", resp.context)
        self.assertIn("STATE_CHOICES", resp.context)
        self.assertIn("SKILL_CHOICES", resp.context)

    # ---------- login_required: event_form ----------
    def test_event_form_requires_login_and_handles_invalid_post(self):
        resp_anon = self.client.get(reverse("event_form"))
        self.assertEqual(resp_anon.status_code, 302)

        self._client_login()
        # GET OK
        resp_get = self.client.get(reverse("event_form"))
        self.assertEqual(resp_get.status_code, 200)

        # POST with incomplete data -> stays on page with error flash
        resp_post = self.client.post(reverse("event_form"), data={"title": ""})
        self.assertEqual(resp_post.status_code, 200)
        self.assertIn(b"Please fix the errors below", resp_post.content)

    # ---------- login_required: volunteer_history (list + filters + export) ----------
    def test_volunteer_history_lists_filters_and_export(self):
        self._client_login()

        # seed a couple of rows
        VP.objects.create(
            volunteer_name="Ada Lovelace",
            event_name="Health Fair",
            description="Vitals station",
            location="City Hall",
            required_skills="CPR, First Aid",
            urgency="High",
            event_date=date(2025, 11, 2),
            capacity_current=3,
            capacity_total=5,
            languages="English, Spanish",
            status="Registered",
        )
        VP.objects.create(
            volunteer_name="Grace Hopper",
            event_name="Park Cleanup",
            description="Trash collection",
            location="Central Park",
            required_skills="",
            urgency="Low",
            event_date=date(2025, 11, 3),
            capacity_current=10,
            capacity_total=20,
            languages="English",
            status="Attended",
        )

        url = reverse("volunteer_history")

        # no filters
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rows", resp.context)
        self.assertGreaterEqual(resp.context["count"], 2)

        # filter by volunteer name and status
        resp_f = self.client.get(url, {"volunteer": "Ada Lovelace", "status": "Registered"})
        self.assertEqual(resp_f.status_code, 200)
        self.assertTrue(all(r["volunteer_name"] == "Ada Lovelace" for r in resp_f.context["rows"]))
        self.assertTrue(all(r["status"] == "Registered" for r in resp_f.context["rows"]))

        # export = 1 should return either XLSX (if openpyxl present) or CSV fallback
        resp_x = self.client.get(url + "?export=1")
        self.assertIn(resp_x.status_code, (200, 206))  # just in case
        ct = resp_x["Content-Type"]
        self.assertTrue(
            ct.startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            or ct.startswith("text/csv")
        )
        self.assertIn("attachment; filename=", resp_x["Content-Disposition"])

    # ---------- login_required: match_volunteer (GET + POST + override rule) ----------
    def test_match_volunteer_get_and_post_flow(self):
        self._client_login()
        url = reverse("match_volunteer")

        # GET: page renders with suggested/selected in context
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn("volunteers", resp_get.context)
        self.assertIn("events", resp_get.context)
        self.assertIn("suggested", resp_get.context)
        self.assertIn("selected", resp_get.context)

        # POST: assign the suggested event to the default volunteer
        # The view itself chooses a default volunteer_id + suggested event,
        # but we'll provide explicit ids using the context lists.
        volunteers = resp_get.context["volunteers"]
        events = resp_get.context["events"]
        vid = str(volunteers[0]["id"])
        eid = str(events[0]["id"])

        resp_post = self.client.post(
            url,
            data={
                "volunteer_id": vid,
                "matched_event": eid,
                "action": "assign",  # or "assign_notify"
                # no override
                "override": "",
                "override_reason": "",
                "admin_notes": "automatic test",
            },
        )
        self.assertEqual(resp_post.status_code, 200)
        self.assertIsNotNone(resp_post.context["saved"])

        # Override requires a reason
        resp_over = self.client.post(
            url,
            data={
                "volunteer_id": vid,
                "matched_event": eid,
                "action": "assign",
                "override": "on",
                "override_reason": "",  # missing -> should error
            },
        )
        self.assertEqual(resp_over.status_code, 200)
        self.assertIn("errors", resp_over.context)
        self.assertTrue(any("Override reason is required" in e for e in resp_over.context["errors"]))

        # Confirm DB updated_or_created an Assignment
        self.assertTrue(
            Assignment.objects.filter(volunteer_id=vid, event_id=eid).exists()
        )
