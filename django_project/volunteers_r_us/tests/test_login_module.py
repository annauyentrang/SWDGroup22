""" Run tests with the following command:

coverage run manage.py test volunteers_r_us -v 2
coverage report -m
coverage html  # optional: opens htmlcov/index.html

"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginModuleTests(TestCase):
    """Covers registration, authentication, and access control for the Login module."""

    def setUp(self):
        self.home_url = reverse("home")
        self.login_url = reverse("login")
        self.register_url = reverse("register")
        self.logout_url = reverse("logout")
        self.profile_url = reverse("profile_form")
        self.event_form_url = reverse("event_form")
        self.match_url = reverse("match_volunteer")
        self.history_url = reverse("volunteer_history")

    # --------------------
    # Registration & Login
    # --------------------

    def test_register_validations(self):
        # Empty submit
        resp = self.client.post(self.register_url, {})
        self.assertContains(resp, "Email is required.", status_code=200)

        # Short password
        resp = self.client.post(self.register_url, {
            "email": "a@b.com", "password": "short", "confirm": "short"
        })
        self.assertContains(resp, "Password must be at least 8 characters.", status_code=200)

        # Mismatched confirm
        resp = self.client.post(self.register_url, {
            "email": "a@b.com", "password": "LongPass123", "confirm": "Different"
        })
        self.assertContains(resp, "Passwords must match.", status_code=200)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="dupe@ex.com", password="ValidPass123")
        resp = self.client.post(self.register_url, {
            "email": "dupe@ex.com", "password": "ValidPass123", "confirm": "ValidPass123"
        })
        self.assertContains(resp, "already exists", status_code=200)

    def test_register_login_logout_happy_path(self):
        # Register
        resp = self.client.post(self.register_url, {
            "email": "new@user.com", "password": "ValidPass123", "confirm": "ValidPass123"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.login_url)

        # Login
        resp = self.client.post(self.login_url, {
            "email": "new@user.com", "password": "ValidPass123"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.home_url)

        # Logout
        resp = self.client.get(self.logout_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.home_url)

    def test_login_invalid_credentials(self):
        User.objects.create_user(email="x@y.com", password="Password123")
        resp = self.client.post(self.login_url, {"email": "x@y.com", "password": "wrong"})
        self.assertContains(resp, "Invalid email or password.", status_code=200)

    def test_password_is_hashed(self):
        u = User.objects.create_user(email="hash@test.com", password="HashedPass123")
        self.assertTrue(u.password.startswith("pbkdf2_"))
        self.assertTrue(u.check_password("HashedPass123"))

    def test_login_redirects_to_next(self):
        User.objects.create_user(email="next@test.com", password="NextPass123")
        next_url = self.profile_url
        resp = self.client.post(self.login_url + f"?next={next_url}", {
            "email": "next@test.com", "password": "NextPass123"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, next_url)

    # --------------------
    # Access Control
    # --------------------

    def test_protected_pages_redirect_when_anonymous(self):
        for url in [self.profile_url, self.event_form_url, self.match_url, self.history_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp.url.startswith(self.login_url + "?next="))

    def test_regular_user_cannot_access_staff_only_match(self):
        u = User.objects.create_user(email="user@ex.com", password="Password123")
        self.client.post(self.login_url, {"email": "user@ex.com", "password": "Password123"})
        resp = self.client.get(self.match_url)
        self.assertIn(resp.status_code, (302, 403))

    def test_staff_user_can_access_match(self):
        s = User.objects.create_user(email="staff@ex.com", password="Password123")
        s.is_staff = True
        s.save()
        self.client.post(self.login_url, {"email": "staff@ex.com", "password": "Password123"})
        resp = self.client.get(self.match_url)
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_user_can_access_profile_and_event_form(self):
        u = User.objects.create_user(email="ok@ex.com", password="Password123")
        self.client.post(self.login_url, {"email": "ok@ex.com", "password": "Password123"})
        for url in [self.profile_url, self.event_form_url, self.history_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
