from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class RegisterTests(APITestCase):
    def test_register_creates_user(self):
        url = reverse('register')
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123",
            "role": User.Role.TENANT,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='existing', password='pass12345')
        url = reverse('register')
        data = {"username": "existing", "password": "anotherpass123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='logintest', password='pass12345')

    def test_login_returns_tokens(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {"username": "logintest", "password": "pass12345"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password_rejected(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {"username": "logintest", "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)