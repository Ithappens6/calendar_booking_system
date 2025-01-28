from rest_framework import serializers
from .models import User
from .models import Availability
from .models import Meeting
from .enums import MeetingStatus
from .utils import convert_to_utc
from datetime import datetime, time, date
import pytz
from django.utils.timezone import now
from .services.booking_service import BookingService

class UserSerializer(serializers.ModelSerializer):
    timezone = serializers.ChoiceField(choices=[(tz, tz) for tz in pytz.all_timezones], default="UTC")
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'timezone']



class AvailabilitySerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])

    class Meta:
        model = Availability
        fields = ['id', 'day_of_week', 'specific_date', 'start_time', 'end_time']


class SetAvailabilitySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    availabilities = AvailabilitySerializer(many=True)

    def validate(self, data):
        user_id = data["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with id={user_id} does not exist.")
        
        
        data["user"] = user
        
        for entry in data["availabilities"]:
            day_of_week = entry.get("day_of_week")
            specific_date = entry.get("specific_date")
            start_time = entry["start_time"]
            end_time = entry["end_time"]

            if day_of_week is None and not specific_date:
                raise serializers.ValidationError(
                    "Each availability must have either 'day_of_week' or 'specific_date'."
                )
            if day_of_week is not None and specific_date:
                raise serializers.ValidationError(
                    "Do not provide both 'day_of_week' and 'specific_date' in one entry."
                )
            
            if start_time >= end_time:
                raise serializers.ValidationError("start_time must be before end_time.")

        return data

    def save(self, **kwargs):
        user = self.validated_data["user"]

        # remove al cached slots
        BookingService.remove_cached_slots(user)


        for entry in self.validated_data["availabilities"]:
            day_of_week = entry.get("day_of_week")
            specific_date = entry.get("specific_date")
            start_time = entry["start_time"]
            end_time = entry["end_time"]
            
            # Delete old records for the same day_of_week or specific_date
            if day_of_week is not None:
                user.availabilities.filter(day_of_week=day_of_week, specific_date__isnull=True).delete()
            elif specific_date is not None:
                user.availabilities.filter(specific_date=specific_date).delete()
            else:
                raise serializers.ValidationError("Each availability must have either 'day_of_week' or 'specific_date'.")
            
            # Create new availability, storing times exactly as the user gave them
            Availability.objects.create(
                calendar_owner=user,
                day_of_week=day_of_week,
                specific_date=specific_date,
                start_time=start_time,  # local time as provided
                end_time=end_time       # local time as provided
            )


class MeetingSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True, required=True)  # Add token as a required field

    class Meta:
        model = Meeting
        fields = ['id', 'calendar_owner', 'invitee_name', 'invitee_email', 'date', 'start_time', 'end_time', 'status', 'token']

    def validate_status(self, value):
        if value not in [status.value for status in MeetingStatus]:
            raise serializers.ValidationError(f"Invalid status: {value}")
        return value

    def validate(self, data):
        # Validate that start_time is before end_time
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before end time.")
        
        # Ensure date is in the present or future
        if data['date'] < now().date():
            raise serializers.ValidationError("The meeting date cannot be in the past.")
        
        return data







