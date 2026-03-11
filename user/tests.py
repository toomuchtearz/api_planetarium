from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

REGISTER_URL = reverse("user:create")
ME_URL = reverse("user:manage")

TOKEN_URL = reverse("token_obtain_pair")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        """Test creating a new user successful"""
        payload = {
            "email": "test@test.com",
            "password": "testpassword123",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_existing_email_fails(self):
        """Test that email must be unique"""
        payload = {
            "email": "test@test.com",
            "password": "testpassword123",
        }
        create_user(**payload)

        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class AuthTokenTests(TestCase):
    """Test JWT Token retrieval"""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "email": "test@test.com",
            "password": "testpassword123",
        }
        self.user = create_user(**self.user_data)

    def test_create_token(self):
        """Test valid login returns a token"""
        res = self.client.post(TOKEN_URL, self.user_data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_create_token_invalid_credentials(self):
        """Test invalid login fails"""
        payload = {
            "email": "test@test.com",
            "password": "WRONGpassword",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ManageUserTests(TestCase):
    """Test the 'Me' endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@test.com",
            password="testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_me(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertEqual(res.data["is_staff"], False)

    def test_post_me_not_allowed(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_me(self):
        """Test updating own profile (password & email)"""

        payload = {
            "password": "newStrongPassword456",
            "email": "newemail@test.com"
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
