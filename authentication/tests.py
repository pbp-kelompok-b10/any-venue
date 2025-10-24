from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("authentication:register")
        self.login_url = reverse("authentication:login")
        self.logout_url = reverse("authentication:logout")

    # ---------- REGISTER TESTS ---------- #
    def test_register_success_user(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "is_owner": "false"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(User.objects.filter(username="alya").exists())

    def test_register_success_owner(self):
        response = self.client.post(self.register_url, {
            "username": "nbl_owner",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "is_owner": "true"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(User.objects.get(username="nbl_owner").profile.role, "OWNER")

    def test_missing_fields(self):
        response = self.client.post(self.register_url, {
            "username": "",
            "password1": "abc",
            "password2": "abc",
        })
        self.assertJSONEqual(response.content, {"success": False, "error": "All fields are required."})

    def test_password_mismatch(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "abc123",
            "password2": "def456",
        })
        self.assertIn("Passwords do not match", response.json()["error"])

    def test_username_taken(self):
        User.objects.create_user(username="alya", password="abc123")
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "abc123",
            "password2": "abc123",
        })
        self.assertIn("Username already taken", response.json()["error"])

    def test_username_too_long(self):
        response = self.client.post(self.register_url, {
            "username": "a" * 151,
            "password1": "abc123456!",
            "password2": "abc123456!",
        })
        self.assertIn("cannot exceed", response.json()["error"])

    def test_username_invalid_chars(self):
        response = self.client.post(self.register_url, {
            "username": "alya<>",
            "password1": "Validpass123!",
            "password2": "Validpass123!",
        })
        self.assertIn("may contain only", response.json()["error"])

    def test_password_too_short(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "123",
            "password2": "123",
        })
        self.assertIn("at least 8", response.json()["error"])

    def test_password_common(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "password",
            "password2": "password",
        })
        self.assertIn("too common", response.json()["error"])

    def test_password_contains_username(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "alya1234",
            "password2": "alya1234",
        })
        self.assertIn("cannot contain", response.json()["error"])

    def test_username_contains_password(self):
        response = self.client.post(self.register_url, {
            "username": "alya1234",
            "password1": "alya",
            "password2": "alya",
        })
        self.assertIn("cannot contain", response.json()["error"])

    def test_password_same_as_username(self):
        response = self.client.post(self.register_url, {
            "username": "alya",
            "password1": "alya",
            "password2": "alya",
        })
        self.assertIn("too similar", response.json()["error"])

    def test_register_get_request(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"register", response.content)

    # ---------- LOGIN TESTS ---------- #
    def test_login_success(self):
        User.objects.create_user(username="alya", password="StrongPass123")
        response = self.client.post(self.login_url, {
            "username": "alya",
            "password": "StrongPass123"
        })
        self.assertTrue(response.json()["success"])

    def test_login_failed(self):
        response = self.client.post(self.login_url, {
            "username": "alya",
            "password": "wrongpass"
        })
        self.assertFalse(response.json()["success"])

    def test_login_get_request(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.content)

    # ---------- LOGOUT TESTS ---------- #
    def test_logout_normal(self):
        User.objects.create_user(username="alya", password="StrongPass123")
        self.client.login(username="alya", password="StrongPass123")
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # redirect to landing page

    def test_logout_ajax(self):
        User.objects.create_user(username="alya", password="StrongPass123")
        self.client.login(username="alya", password="StrongPass123")
        response = self.client.get(self.logout_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(response.json()["success"])
