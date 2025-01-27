from django.test import TestCase
from datetime import date, time, datetime
from core.utils import convert_to_utc
import pytz

class UtilsTestCase(TestCase):
    def test_convert_to_utc(self):
        # Test conversion from EST to UTC
        est_date = date(2023, 10, 1)
        est_time = time(12, 0, 0)
        est_timezone = 'America/New_York'
        expected_utc_time = pytz.UTC.localize(datetime(2023, 10, 1, 16, 0, 0))
        self.assertEqual(convert_to_utc(est_date, est_time, est_timezone), expected_utc_time)

        # Test conversion from PST to UTC
        pst_date = date(2023, 10, 1)
        pst_time = time(12, 0, 0)
        pst_timezone = 'America/Los_Angeles'
        expected_utc_time = pytz.UTC.localize(datetime(2023, 10, 1, 19, 0, 0))
        self.assertEqual(convert_to_utc(pst_date, pst_time, pst_timezone), expected_utc_time)

        # Test conversion from IST to UTC
        ist_date = date(2023, 10, 1)
        ist_time = time(12, 0, 0)
        ist_timezone = 'Asia/Kolkata'
        expected_utc_time = pytz.UTC.localize(datetime(2023, 10, 1, 6, 30, 0))
        self.assertEqual(convert_to_utc(ist_date, ist_time, ist_timezone), expected_utc_time)