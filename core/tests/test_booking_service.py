from django.test import TestCase
from unittest.mock import MagicMock, patch
from datetime import datetime, time, timedelta, date
from core.models import Availability, Meeting
from django.core.cache import cache
from core.services.booking_service import BookingService

class BookingServiceTestCase(TestCase):
    def setUp(self):
        self.calendar_owner = MagicMock()
        self.calendar_owner.id = 1
        self.calendar_owner.availabilities = MagicMock()
        self.calendar_owner.meetings = MagicMock()

        self.mock_availabilities = [
            MagicMock(start_time=time(9, 0), end_time=time(12, 0), specific_date=None, day_of_week=0)
        ]

        self.mock_meetings = [
            MagicMock(start_time=time(10, 0), end_time=time(11, 0), date=date.today(), status='booked'),
        ]

    def test_get_available_slots_cached(self):
        search_date = date.today()
        cache_key = f"timeslots_user_{self.calendar_owner.id}_{search_date}"
        cache.set(cache_key, [{'start_time': '09:00:00', 'end_time': '10:00:00'}], timeout=3600)

        result = BookingService.get_available_slots(self.calendar_owner, search_date)

        self.assertEqual(result, [{'start_time': '09:00:00', 'end_time': '10:00:00'}])
        cache.delete(cache_key)

    def test_get_available_slots_no_cache(self):
        search_date = date(2025, 1, 27)

        # Mock availabilities filter and exists behavior
        mock_availability_queryset = MagicMock()
        mock_availability_queryset.exists.return_value = True
        mock_availability_queryset.__iter__.return_value = iter(self.mock_availabilities)
        
        self.calendar_owner.availabilities.filter.return_value = mock_availability_queryset

        # Mock meetings.filter() behavior
        self.calendar_owner.meetings.filter.return_value = self.mock_meetings

        # Mock meetings filter behavior
        self.calendar_owner.meetings.filter.return_value = self.mock_meetings

        # Call the method being tested
        result = BookingService.get_available_slots(self.calendar_owner, search_date)


        expected_slots = {
            'calendar_owner': self.calendar_owner.id,
            'search_date': search_date,
            'time_slots': [{'start_time': time(9, 0), 'end_time': time(10, 0)},
                           {'start_time': time(11, 0), 'end_time': time(12, 0)}]
        }
        # Assert results
        self.assertEqual(result, expected_slots)

    def test_generate_booking_token(self):
        token = BookingService.generate_booking_token(1, date.today())

        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_validate_token_and_slot(self):
        token = 'valid_token'
        available_slots = {
            'calendar_owner': self.calendar_owner.id,
            'search_date': date.today(),
            'time_slots': [
                {'start_time': time(9, 0), 'end_time': time(10, 0)},
            ],
        }

        cache.set(token, available_slots, timeout=3600)

        try:
            BookingService.validate_token_and_slot(
                self.calendar_owner, token, date.today(), time(9, 0), time(10, 0)
            )
        except ValueError:
            self.fail("validate_token_and_slot raised ValueError unexpectedly!")

        cache.delete(token)

    def test_validate_token_and_slot_invalid_token(self):
        with self.assertRaises(ValueError):
            BookingService.validate_token_and_slot(
                self.calendar_owner, 'invalid_token', date.today(), time(9, 0), time(10, 0)
            )
    
    def test_validate_token_and_slot_invalid_calendar_owner(self):
        token = 'valid_token'
        available_slots = {
            'calendar_owner': 2,
            'search_date': date.today(),
            'time_slots': [
                {'start_time': time(9, 0), 'end_time': time(10, 0)},
            ],
        }

        cache.set(token, available_slots, timeout=3600)
        with self.assertRaises(ValueError):
            BookingService.validate_token_and_slot(
                self.calendar_owner, token, date.today(), time(9, 0), time(10, 0)
            )
    
    def test_validate_token_and_slot_invalid_date(self):
        token = 'valid_token'
        available_slots = {
            'calendar_owner': self.calendar_owner.id,
            'search_date': date.today() - timedelta(days=1),
            'time_slots': [
                {'start_time': time(9, 0), 'end_time': time(10, 0)},
            ],
        }
        cache.set(token, available_slots, timeout=3600)
        with self.assertRaises(ValueError):
            BookingService.validate_token_and_slot(
                self.calendar_owner, token, date.today(), time(9, 0), time(10, 0)
            )
    
    def test_validate_token_and_slot_invalid_slot(self):
        token = 'valid_token'
        available_slots = {
            'calendar_owner': self.calendar_owner.id,
            'search_date': date.today(),
            'time_slots': [
                {'start_time': time(9, 0), 'end_time': time(10, 0)},
            ],
        }
        cache.set(token, available_slots, timeout=3600)
        with self.assertRaises(ValueError):
            BookingService.validate_token_and_slot(
                self.calendar_owner, token, date.today(), time(10, 0), time(11, 0)
            )


    @patch('core.models.Meeting.objects.filter')
    def test_validate_no_overlap(self, mock_filter):
        mock_filter.return_value.exists.return_value = False

        try:
            BookingService.validate_no_overlap(self.calendar_owner, date.today(), time(9, 0), time(10, 0))
        except ValueError:
            self.fail("validate_no_overlap raised ValueError unexpectedly!")

        mock_filter.return_value.exists.return_value = True
        with self.assertRaises(ValueError):
            BookingService.validate_no_overlap(self.calendar_owner, date.today(), time(9, 0), time(10, 0))

    @patch('core.models.Availability.objects.filter')
    def test_validate_availability(self, mock_filter):
        # First call: No specific availability, Second call: No default availability
        mock_filter.return_value.exists.side_effect = [False, True]

        # Should pass without raising an exception
        try:
            BookingService.validate_availability(
                self.calendar_owner, datetime.now(), datetime.now() + timedelta(hours=1)
            )
        except ValueError:
            self.fail("validate_availability raised ValueError unexpectedly!")