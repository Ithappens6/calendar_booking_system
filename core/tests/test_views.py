from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User, Availability, Meeting
from datetime import time, date
import json

class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {"name": "John Doe", "email": "johndoe@example.com", "timezone": "UTC"}

    def test_create_user(self):
        response = self.client.post(reverse('user-list-create'), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], self.user_data['name'])

    def test_get_users(self):
        User.objects.create(**self.user_data)
        response = self.client.get(reverse('user-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class UserDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(name="Jane Doe", email="janedoe@example.com", timezone="UTC")

    def test_get_user(self):
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.user.name)

    def test_update_user(self):
        data = {"name": "Updated Jane", "email": "janedoe@example.com", "timezone": "UTC"}
        response = self.client.put(reverse('user-detail', kwargs={'pk': self.user.id}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

    def test_delete_user(self):
        response = self.client.delete(reverse('user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)


class AvailabilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(name="John Doe", email="johndoe@example.com", timezone="UTC")
        self.availability_data = {
            "user_id": self.user.id,
            "availabilities": [
                {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}
            ]
        }

    def test_set_availability(self):
        response = self.client.post(reverse('set-availability'), data=json.dumps(self.availability_data),
    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.availabilities.count(), 1)


class MeetingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(name="John Doe", email="johndoe@example.com", timezone="UTC")
        self.meeting_data = {
            "calendar_owner": self.user.id,
            "invitee_name": "Alice",
            "invitee_email": "alice@example.com",
            "date": date.today().isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "status": "pending",
            "token": "some-token"
        }

    def test_list_meetings(self):
        Meeting.objects.create(
            calendar_owner=self.user,
            invitee_name="Alice",
            invitee_email="alice@example.com",
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status="pending"
        )
        response = self.client.get(reverse('list-meetings', kwargs={'user_id': self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    @patch('core.views.BookingService.validate_token_and_slot', return_value=True)
    def test_book_appointment(self, mock_validate_token_and_slot):
        mock_validate_token_and_slot.return_value = True
        response = self.client.post(reverse('book-appointment'), data=json.dumps(self.meeting_data), content_type="application/json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meeting.objects.count(), 1)

    def test_search_available_slots(self):
        Availability.objects.create(
            calendar_owner=self.user,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        response = self.client.get(
            reverse('search-available-slots', kwargs={'user_id': self.user.id}),
            {"date": date.today().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("available_slots", response.data)
