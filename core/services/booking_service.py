from django.utils.timezone import make_aware
from django.core.cache import cache
from datetime import datetime, timedelta
from django.db.models import Q
from core.models import Meeting, Availability, CachedKey
import hashlib
import uuid, pytz


class BookingService:
    @staticmethod
    def get_available_slots(calendar_owner, search_date):
        """
        Get available time slots for a calendar owner on a specific date.
        """
        # --- 1) Check if cached results exist ---
        cache_key = f"timeslots_user_{calendar_owner.id}_{search_date}"
        cached_slots = cache.get(cache_key)
        if cached_slots:
            return cached_slots

        availabilities = calendar_owner.availabilities.filter(
            specific_date=search_date
        )

        if not availabilities.exists():
            availabilities = calendar_owner.availabilities.filter(
                specific_date__isnull=True,
                day_of_week=search_date.weekday()
            )

        # --- 3) Fetch relevant meetings on this date ---
        meetings = calendar_owner.meetings.filter(
            date=search_date,
            status__in=['booked', 'rescheduled']
        )

        # --- 4) Generate 1-hour slots for each availability and filter out overlaps ---
        time_slots = []
        for availability in availabilities:
            start_datetime = datetime.combine(search_date, availability.start_time)
            end_datetime = datetime.combine(search_date, availability.end_time)

            current_start = start_datetime
            while current_start + timedelta(hours=1) <= end_datetime:
                current_end = current_start + timedelta(hours=1)

                # Check overlap with any meeting
                if not any(
                    (current_start.time() < m.end_time and current_end.time() > m.start_time)
                    for m in meetings
                ):
                    time_slots.append({
                        "start_time": current_start.time(),  # Use time() to extract time part
                        "end_time": current_end.time()      # Use time() to extract time part
                    })

                current_start = current_end
        
        availabile_slots = {}
        availabile_slots['calendar_owner'] = calendar_owner.id
        availabile_slots['search_date'] = search_date
        availabile_slots['time_slots'] = time_slots

        # --- 5) Cache the time slots for performance ---
        cache.set(cache_key, availabile_slots, timeout=3600)  # 1 hour

        # store the cache key in the database
        CachedKey.objects.create(owner_id=calendar_owner.id, cache_key=cache_key)   

        return availabile_slots


    @staticmethod
    def generate_booking_token(calendar_owner_id, search_date):
        """
        Generate a unique booking token for a search request.
        """
        token = hashlib.sha256(f"{calendar_owner_id}_{search_date}_{uuid.uuid4()}".encode()).hexdigest()
        return token

    @staticmethod
    def remove_cached_slots(calendar_owner, search_date=None):
        """
        Remove cached time slots for a calendar owner after a booking.
        """
        if search_date:
            cache_key = f"timeslots_user_{calendar_owner.id}_{search_date}"
            cache.delete(cache_key)
        else:
            keys = CachedKey.objects.filter(owner_id=calendar_owner.id).values_list('cache_key', flat=True)
            for key in keys:
                cache.delete(key)
            # Clear all entries for this owner in the database
            CachedKey.objects.filter(owner_id=calendar_owner.id).delete()

    @staticmethod
    def remove_cached_token(token):
        """
        Remove cached token after a booking.
        """
        cache.delete(token)


    @staticmethod
    def validate_token_and_slot(calendar_owner, token, date, start_time, end_time):
        """
        Validate if the token is valid and the requested slot is available.
        """
        available_slots = cache.get(token)
        if not available_slots:
            raise ValueError("Invalid or expired token. Please search for available slots again.")
        
        if calendar_owner.id != available_slots['calendar_owner']:
            raise ValueError("The token does not match the calendar owner.")
        
        if date != available_slots['search_date']:
            raise ValueError("The token does not match the search date.")
        

        # Check if the requested slot matches the token's available slots
        start_time = start_time
        end_time = end_time
        slot_matches = any(
            slot['start_time'] == start_time and 
            slot['end_time'] == end_time
            for slot in available_slots['time_slots']
        )
        if not slot_matches:
            raise ValueError("The requested time slot was not retrieved from the available slots.")

    @staticmethod
    def validate_availability(calendar_owner, start_time, end_time):
        """
        Validate if the requested time slot is available for the calendar owner.
        """
        specific_availability = calendar_owner.availabilities.filter(
            specific_date=start_time.date(),
            start_time__lte=start_time.time(),
            end_time__gte=end_time.time()
        ).exists()

        # Check default availability if no specific rules exist
        if not specific_availability:
            default_availability = calendar_owner.availabilities.filter(
                specific_date__isnull=True,
                day_of_week=start_time.weekday(),
                start_time__lte=start_time.time(),
                end_time__gte=end_time.time()
            ).exists()

            if not default_availability:
                raise ValueError("The requested time does not fit into any available time slot.")

    @staticmethod
    def validate_no_overlap(calendar_owner, date, start_time, end_time):
        """
        Validate if the requested time slot overlaps with existing meetings.
        """
        overlapping_meetings = Meeting.objects.filter(
            calendar_owner=calendar_owner,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['booked', 'rescheduled']
        ).exists()
        if overlapping_meetings:
            raise ValueError("The requested time slot is already booked.")
