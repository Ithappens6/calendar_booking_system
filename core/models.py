from django.db import models
from .enums import MeetingStatus
import pytz

# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    timezone = models.CharField(
        max_length=100,
        default='UTC',
        choices=[(timezone, timezone) for timezone in pytz.all_timezones])

    def __str__(self):
        return self.name


class Availability(models.Model):
    calendar_owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(
        choices=[(i, day) for i, day in enumerate([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])],
        null=True, blank=True
    )
    specific_date = models.DateField(null=True, blank=True)  # Optional for specific days
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        if self.specific_date:
            return f"{self.calendar_owner.name} - {self.specific_date} ({self.start_time} to {self.end_time})"
        return f"{self.calendar_owner.name} - {self.get_day_of_week_display()} ({self.start_time} to {self.end_time})"
    


class Meeting(models.Model):
    STATUS_CHOICES = MeetingStatus.choices()

    calendar_owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='meetings')
    invitee_name = models.CharField(max_length=100)
    invitee_email = models.EmailField()
    date = models.DateField()  # New date field
    start_time = models.TimeField()  # Changed to TimeField
    end_time = models.TimeField()  # Changed to TimeField
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=MeetingStatus.PENDING
    )

    token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)  # Auto-updates on save

    def __str__(self):
        return f"Meeting with {self.invitee_name} on {self.date} at {self.start_time} ({self.status})"


class CachedKey(models.Model):
    owner_id = models.IntegerField()
    cache_key = models.CharField(max_length=255)
