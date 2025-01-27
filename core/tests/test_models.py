from django.test import TestCase
from core.models import User, Availability, Meeting
from core.enums import MeetingStatus
import pytz


class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create(name="John Doe", email="john@example.com", timezone="UTC")
        self.assertEqual(str(user), "John Doe")
        self.assertEqual(user.timezone, "UTC")

    def test_user_timezone_choices(self):
        user = User.objects.create(name="Jane Smith", email="jane@example.com", timezone="Asia/Kolkata")
        self.assertIn(user.timezone, pytz.all_timezones)


class AvailabilityModelTest(TestCase):
    def test_availability_creation(self):
        user = User.objects.create(name="John Doe", email="john@example.com", timezone="UTC")
        availability = Availability.objects.create(
            calendar_owner=user,
            day_of_week=0,
            start_time="09:00:00",
            end_time="10:00:00"
        )
        self.assertEqual(str(availability), f"{user.name} - Monday (09:00:00 to 10:00:00)")

    def test_availability_creation_specific_date(self):
        user = User.objects.create(name="John Doe", email="john@example.com", timezone="UTC")
        availability = Availability.objects.create(
            calendar_owner=user,
            specific_date="2025-01-01",
            start_time="09:00:00",
            end_time="10:00:00"
        )
        self.assertEqual(str(availability), f"{user.name} - 2025-01-01 (09:00:00 to 10:00:00)")


class MeetingModelTest(TestCase):
    def test_meeting_creation(self):
        user = User.objects.create(name="John Doe", email="john@example.com", timezone="UTC")
        meeting = Meeting.objects.create(
            calendar_owner=user,
            invitee_name="Invitee Name",
            invitee_email="invitee@example.com",
            date="2025-01-01",
            start_time="10:00:00",
            end_time="11:00:00",
            status=MeetingStatus.BOOKED.value
        )
        self.assertEqual(str(meeting), "Meeting with Invitee Name on 2025-01-01 at 10:00:00 (booked)")

    def test_meeting_default_status(self):
        user = User.objects.create(name="John Doe", email="john@example.com", timezone="UTC")
        meeting = Meeting.objects.create(
            calendar_owner=user,
            invitee_name="Invitee Name",
            invitee_email="invitee@example.com",
            date="2025-01-01",
            start_time="10:00:00",
            end_time="11:00:00",
        )
        self.assertEqual(meeting.status, MeetingStatus.PENDING)
