from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from datetime import time, date
from core.models import User, Availability, Meeting
from core.serializers import (
    UserSerializer,
    AvailabilitySerializer,
    SetAvailabilitySerializer,
    MeetingSerializer,
)
from core.enums import MeetingStatus

class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            'id': 1,
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'timezone': 'UTC',
        }

    def test_user_serializer(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'John Doe')
        self.assertEqual(serializer.validated_data['timezone'], 'UTC')


class AvailabilitySerializerTestCase(TestCase):
    def setUp(self):
        self.availability_data = {
            'day_of_week': 1,
            'specific_date': None,
            'start_time': time(9, 0),
            'end_time': time(17, 0),
        }

    def test_availability_serializer(self):
        serializer = AvailabilitySerializer(data=self.availability_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)  # Include serializer.errors for debugging
        self.assertEqual(serializer.validated_data['start_time'], time(9, 0))
        self.assertEqual(serializer.validated_data['end_time'], time(17, 0))


class SetAvailabilitySerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(name='John Doe', email='johndoe@example.com')
        self.availability_data = {
            'user_id': self.user.id,
            'availabilities': [
                {
                    'day_of_week': 1,
                    'specific_date': None,
                    'start_time': '09:00',
                    'end_time': '17:00',
                },
            ],
        }

    def test_set_availability_serializer(self):
        serializer = SetAvailabilitySerializer(data=self.availability_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)  # Include serializer.errors for debugging
        self.assertEqual(serializer.validated_data['user'], self.user)

    def test_invalid_availability(self):
        invalid_data = {
            'user_id': self.user.id,
            'availabilities': [
                {
                    'day_of_week': None,
                    'specific_date': None,
                    'start_time': '09:00',
                    'end_time': '08:00',  # End time is before start time
                },
            ],
        }

        serializer = SetAvailabilitySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid(), serializer.errors)  # Ensure serializer is invalid
        self.assertIn('non_field_errors', serializer.errors)  # Check for non_field_errors
        self.assertIn(
            "Each availability must have either 'day_of_week' or 'specific_date'.",
            [str(e) for e in serializer.errors['non_field_errors']]
        )

    def test_user_not_found(self):
        invalid_data = {
            'user_id': 999,  # Non-existent user ID
            'availabilities': [
                {
                    'day_of_week': 1,
                    'specific_date': None,
                    'start_time': '09:00',
                    'end_time': '17:00',
                },
            ],
        }

        serializer = SetAvailabilitySerializer(data=invalid_data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        
        # Check the error exists in non_field_errors
        self.assertIn('non_field_errors', context.exception.detail)
        self.assertIn("User with id=999 does not exist.", [str(e) for e in context.exception.detail['non_field_errors']])


    def test_save_method(self):
        serializer = SetAvailabilitySerializer(data=self.availability_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(self.user.availabilities.count(), 1)
        availability = self.user.availabilities.first()
        self.assertEqual(availability.day_of_week, 1)
        self.assertIsNone(availability.specific_date)
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))



class MeetingSerializerTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(id=1, name='John Doe', email='johndoe@example.com')
        self.meeting_data = {
            'calendar_owner': self.user.id,
            'invitee_name': 'Jane Doe',
            'invitee_email': 'janedoe@example.com',
            'date': date.today(),
            'start_time': time(10, 0),
            'end_time': time(11, 0),
            'status': MeetingStatus.PENDING.value,
            'token': 'test-token',
        }

    def test_meeting_serializer(self):
        serializer = MeetingSerializer(data=self.meeting_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)  # Ensure the serializer is valid
        self.assertEqual(serializer.validated_data['invitee_name'], 'Jane Doe')
        self.assertEqual(serializer.validated_data['status'], MeetingStatus.PENDING.value)

    def test_invalid_meeting_date(self):
        invalid_data = self.meeting_data.copy()
        invalid_data['date'] = date(2020, 1, 1)  # Past date

        serializer = MeetingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid(), serializer.errors)  # Ensure the serializer is invalid
        self.assertIn('non_field_errors', serializer.errors)  # Check for non_field_errors
        self.assertEqual(
            serializer.errors['non_field_errors'][0],
            "The meeting date cannot be in the past."
        )

    def test_invalid_meeting_time(self):
        invalid_data = self.meeting_data.copy()
        invalid_data['start_time'] = time(11, 0)
        invalid_data['end_time'] = time(10, 0)  # End time before start time

        serializer = MeetingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid(), serializer.errors)  # Ensure the serializer is invalid
        self.assertIn('non_field_errors', serializer.errors)  # Check for non_field_errors
        self.assertEqual(
            serializer.errors['non_field_errors'][0],
            "Start time must be before end time."
        )

