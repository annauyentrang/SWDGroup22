import json
from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from volunteers_r_us import views
from volunteers_r_us.models import Event, Skill, Assignment

User = get_user_model()


class MainViewsTests(TestCase):
    def setUp(self):
        self.email = "ada@example.com"
        self.password = "Str0ngPa$$w0rd!"
        self.user = User.objects.create_user(email=self.email, password=self.password)
        self.user.is_staff = True
        self.user.save()

    # ---------- helpers ----------
    def _client_login(self):
        username_field = User.USERNAME_FIELD
        return self.client.login(**{username_field: self.email, "password": self.password})

    # ---------- public / auth views ----------
    def test_home_renders(self):
        url = reverse("home")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_register_valid_then_login_success(self):
        url = reverse("register")
        payload = {
            "email": "newuser@example.com",
            "password": "B3tterPa$$word!",
            "confirm": "B3tterPa$$word!",
        }
        resp = self.client.post(url, data=payload, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

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
        resp_anon = self.client.get(reverse("profile_form"))
        self.assertEqual(resp_anon.status_code, 302)

        self._client_login()
        resp = self.client.get(reverse("profile_form"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)
        self.assertIn("STATE_CHOICES", resp.context)
        self.assertIn("SKILL_CHOICES", resp.context)

    # ---------- login_required: event_form ----------
    def test_event_form_requires_login_and_handles_invalid_post(self):
        resp_anon = self.client.get(reverse("event_form"))
        self.assertEqual(resp_anon.status_code, 302)

        self._client_login()
        resp_get = self.client.get(reverse("event_form"))
        self.assertEqual(resp_get.status_code, 200)

        # invalid POST to keep branch covered
        resp_post = self.client.post(reverse("event_form"), data={"title": ""})
        self.assertEqual(resp_post.status_code, 200)
        self.assertIn(b"Please fix the errors below", resp_post.content)

    # ---------- login_required: volunteer_history (list + filters + export) ----------
    def test_volunteer_history_lists_filters_and_export(self):
        self._client_login()

        # seed volunteers + events + assignments (matches current view logic)
        v1 = User.objects.create_user(email="vol1@example.com", password="pass12345")
        v2 = User.objects.create_user(email="vol2@example.com", password="pass12345")

        e1 = Event.objects.create(
            name="Health Fair",
            description="Vitals station",
            location="City Hall",
            urgency="High",
            event_date=date(2025, 11, 2),
        )
        e2 = Event.objects.create(
            name="Park Cleanup",
            description="Trash collection",
            location="Central Park",
            urgency="Low",
            event_date=date(2025, 11, 3),
        )

        Assignment.objects.create(
            volunteer=v1, event=e1, status=Assignment.ASSIGNED
        )
        Assignment.objects.create(
            volunteer=v2, event=e2, status=Assignment.ATTENDED
        )

        url = reverse("volunteer_history")

        # no filters
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rows", resp.context)
        self.assertGreaterEqual(resp.context["count"], 2)

        # filter by volunteer EMAIL and status (matches view)
        resp_f = self.client.get(url, {"volunteer": "vol1@example.com", "status": Assignment.ASSIGNED})
        self.assertEqual(resp_f.status_code, 200)
        self.assertTrue(all(r["volunteer_id"] == "vol1@example.com" for r in resp_f.context["rows"]))
        self.assertTrue(all(r["status"] == Assignment.ASSIGNED for r in resp_f.context["rows"]))

        # export = 1 should return either XLSX (if openpyxl present) or CSV fallback
        resp_x = self.client.get(url + "?export=1")
        self.assertIn(resp_x.status_code, (200, 206))
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

        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn("volunteers", resp_get.context)
        self.assertIn("events", resp_get.context)
        self.assertIn("suggested", resp_get.context)
        self.assertIn("selected", resp_get.context)

        volunteers = resp_get.context["volunteers"]
        events = resp_get.context["events"]
        vid = str(volunteers[0]["id"])
        eid = str(events[0]["id"])

        resp_post = self.client.post(
            url,
            data={
                "volunteer_id": vid,
                "matched_event": eid,
                "action": "assign",
                "override": "",
                "override_reason": "",
                "admin_notes": "automatic test",
            },
        )
        self.assertEqual(resp_post.status_code, 200)
        self.assertIsNotNone(resp_post.context["saved"])

        resp_over = self.client.post(
            url,
            data={
                "volunteer_id": vid,
                "matched_event": eid,
                "action": "assign",
                "override": "on",
                "override_reason": "",
            },
        )
        self.assertEqual(resp_over.status_code, 200)
        self.assertIn("errors", resp_over.context)
        self.assertTrue(any("Override reason is required" in e for e in resp_over.context["errors"]))

        self.assertTrue(
            Assignment.objects.filter(volunteer_id=vid, event_id=eid).exists()
        )


class EventFormExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="staff@example.com", password="pass12345")
        self.user.is_staff = True
        self.user.save()
        self.client.login(**{User.USERNAME_FIELD: "staff@example.com", "password": "pass12345"})

        s1 = Skill.objects.create(name="CPR")
        s2 = Skill.objects.create(name="First Aid")
        e = Event.objects.create(
            name="Health Fair",
            description="Vitals",
            location="City Hall",
            urgency="High",
            event_date=date(2025, 11, 2),
        )
        e.required_skills.add(s1, s2)

    def test_event_form_export_csv(self):
        url = reverse("event_form") + "?export=1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Type"].startswith("text/csv"))
        self.assertIn("attachment; filename=", resp["Content-Disposition"])
        self.assertIn("Health Fair", resp.content.decode())


class EventFormPdfBranchTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staffpdf@example.com", password="pass12345")
        self.staff.is_staff = True
        self.staff.save()
        self.client.login(**{User.USERNAME_FIELD: "staffpdf@example.com", "password": "pass12345"})

    @patch("volunteers_r_us.views._pdf_table_response")
    def test_event_form_export_pdf_branch(self, mock_pdf):
        mock_pdf.return_value = HttpResponse(b"%PDF-1.4", content_type="application/pdf")
        resp = self.client.get(reverse("event_form") + "?export_pdf=1")
        self.assertEqual(resp.status_code, 200)
        mock_pdf.assert_called_once()


class VolunteerHistoryPdfAndResetTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff3@example.com", password="pass12345")
        self.staff.is_staff = True
        self.staff.save()
        self.client.login(**{User.USERNAME_FIELD: "staff3@example.com", "password": "pass12345"})

        self.volunteer = User.objects.create_user(email="vol@example.com", password="pass12345")
        evt = Event.objects.create(
            name="Park Cleanup",
            description="Trash",
            location="Central Park",
            urgency="Low",
            event_date=date(2025, 11, 3),
        )
        Assignment.objects.create(
            volunteer=self.volunteer,
            event=evt,
            status=Assignment.ASSIGNED,
        )

    @patch("volunteers_r_us.views._pdf_table_response")
    def test_volunteer_history_export_pdf_branch(self, mock_pdf):
        mock_pdf.return_value = HttpResponse(b"%PDF-1.4", content_type="application/pdf")
        url = reverse("volunteer_history") + "?export_pdf=1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        mock_pdf.assert_called_once()

    def test_volunteer_history_reset_redirect(self):
        url = reverse("volunteer_history") + "?reset=1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)


class ViewsHelperTests(TestCase):
    def test_parse_date_multiple_formats_and_invalid(self):
        self.assertEqual(views._parse_date("2025-11-02").isoformat(), "2025-11-02")
        self.assertEqual(views._parse_date("11/02/2025").isoformat(), "2025-11-02")
        self.assertEqual(views._parse_date("2025/11/02").isoformat(), "2025-11-02")
        self.assertIsNone(views._parse_date("not-a-date"))
        self.assertIsNone(views._parse_date(""))

    def test_csv_from_list_skips_empty(self):
        self.assertEqual(views._csv_from_list(["A", "", None, "B"]), "A, B")

    def test_skills_list_handles_none(self):
        self.assertEqual(views._skills_list(None), [])
