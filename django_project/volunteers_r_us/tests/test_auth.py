from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthFlowTests(TestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.home_url = reverse("home")

    def test_register_requires_fields_and_validations(self):
        # empty post
        resp = self.client.post(self.register_url, {})
        self.assertContains(resp, "Email is required.", status_code=200)

        # short password
        resp = self.client.post(self.register_url, {
            "email": "a@b.com",
            "password": "short",
            "confirm": "short"
        })
        self.assertContains(resp, "Password must be at least 8 characters.", status_code=200)

        # mismatch
        resp = self.client.post(self.register_url, {
            "email": "a@b.com",
            "password": "longenough1",
            "confirm": "different"
        })
        self.assertContains(resp, "Passwords must match.", status_code=200)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="a@b.com", password="longenough1")
        resp = self.client.post(self.register_url, {
            "email": "a@b.com",
            "password": "longenough1",
            "confirm": "longenough1"
        })
        self.assertContains(resp, "already exists", status_code=200)

    def test_register_success_then_login_success(self):
        # register
        resp = self.client.post(self.register_url, {
            "email": "new@user.com",
            "password": "ValidPass123",
            "confirm": "ValidPass123"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.login_url)

        # login
        resp = self.client.post(self.login_url, {
            "email": "new@user.com",
            "password": "ValidPass123"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.home_url)

    def test_login_invalid_credentials(self):
        # user exists
        User.objects.create_user(email="x@y.com", password="Password123")
        # wrong password
        resp = self.client.post(self.login_url, {"email": "x@y.com", "password": "nope"})
        self.assertContains(resp, "Invalid email or password.", status_code=200)

    def test_logout(self):
        u = User.objects.create_user(email="x@y.com", password="Password123")
        self.client.post(self.login_url, {"email": "x@y.com", "password": "Password123"})
        resp = self.client.get(self.logout_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.home_url)
