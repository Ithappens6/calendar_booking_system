from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Meeting, Availability
from .serializers import UserSerializer
from .serializers import SetAvailabilitySerializer
from .serializers import MeetingSerializer
from .enums import MeetingStatus
from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination
from .pagenation import MeetingPagination
from django.core.cache import cache
from datetime import datetime
from .services.booking_service import BookingService
from .utils import convert_to_utc
import pytz
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class UserListCreateView(APIView):
    """
    Handles listing all users and creating a new user.
    """
    # decorate with swagger_auto_schema for this get method
    @swagger_auto_schema(
        operation_description="Get all users",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserSerializer,
        responses={201: UserSerializer()}
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    Handles retrieving, updating, and deleting a single user.
    """
    @swagger_auto_schema(
        operation_description="Get a user by ID",
        responses={200: UserSerializer()}
    )
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update a user by ID",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete a user by ID",
        responses={204: "No content"}
    )
    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        


class SetAvailabilityView(APIView):
    """
    API to set availability for a calendar owner.
    """
    @swagger_auto_schema(
        operation_description="Set availability for a calendar owner",
        request_body=SetAvailabilitySerializer,
        responses={201: "Availability set successfully"}
    )
    def post(self, request, *args, **kwargs):
        serializer = SetAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Availability set successfully"}, status=status.HTTP_201_CREATED)




class ListMeetingsView(APIView):
    """
    API to list all meetings for a given calendar owner, with optional date filters and pagination.
    """
    @swagger_auto_schema(
        operation_description="List all meetings for a calendar owner",
        manual_parameters=[
            openapi.Parameter(
                name='start_date',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Filter meetings starting from this date (YYYY-MM-DD)',
                required=False
            ),
            openapi.Parameter(
                name='end_date',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Filter meetings ending on this date (YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={200: MeetingSerializer(many=True)}
    )

    def get(self, request, user_id):
        try:
            calendar_owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get optional query parameters for filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Filter meetings and exclude cancelled ones
        meetings = calendar_owner.meetings.exclude(status=MeetingStatus.CANCELLED.value)

        if start_date:
            start_date_parsed = parse_date(start_date)
            if not start_date_parsed:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
            meetings = meetings.filter(start_time__date__gte=start_date_parsed)

        if end_date:
            end_date_parsed = parse_date(end_date)
            if not end_date_parsed:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
            meetings = meetings.filter(end_time__date__lte=end_date_parsed)

        # Apply pagination
        paginator = MeetingPagination()
        paginated_meetings = paginator.paginate_queryset(meetings, request)

        # Serialize and return paginated response
        serializer = MeetingSerializer(paginated_meetings, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class SearchAvailableSlotsView(APIView):
    """
    API to search available slots for a given calendar owner on a specific date.
    """
    @swagger_auto_schema(
        operation_description="Search available slots for a calendar owner on a specific date",
        manual_parameters=[
            openapi.Parameter(
                name='date',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Search date (YYYY-MM-DD)',
                required=True
            ),
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING),
                'available_slots': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'start_time': openapi.Schema(type=openapi.TYPE_STRING),
                            'end_time': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            }
        )}
    )
    def get(self, request, user_id):
        # Fetch the calendar owner ---
        try:
            calendar_owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Parse the requested date (YYYY-MM-DD) ---
        search_date_str = request.query_params.get('date')
        if not search_date_str:
            return Response(
                {"error": "Date is required (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            search_date = datetime.strptime(search_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch available slots (no timezone logic) ---
        time_slots = BookingService.get_available_slots(calendar_owner, search_date)

        # Generate booking token (optional, not timezone-related) ---
        token = BookingService.generate_booking_token(calendar_owner.id, search_date)

        # Save the time_slots in the cache under the token (valid for 1 hour)
        cache.set(token, time_slots, timeout=3600)

        # Return the response ---
        return Response(
            {"token": token, "available_slots": time_slots},
            status=status.HTTP_200_OK
        )


    

class BookAppointmentView(APIView):
    """
    API to book an appointment for a given calendar owner on a specific date and time slot."""
    @swagger_auto_schema(
        operation_description="Book an appointment for a calendar owner on a specific date and time slot",
        request_body=MeetingSerializer,
        responses={201: MeetingSerializer()}
    )
    def post(self, request):
        serializer = MeetingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        calendar_owner = serializer.validated_data['calendar_owner']
        date = serializer.validated_data['date']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        token = serializer.validated_data['token']

        try:
            # Validate token and slot
            BookingService.validate_token_and_slot(calendar_owner, token, date, start_time, end_time)

            # Validate overlapping meetings
            BookingService.validate_no_overlap(calendar_owner, date, start_time, end_time)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Save the meeting
        serializer.save(
            calendar_owner=calendar_owner,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status='booked'
        )

        # Remove cached time slots for the calendar owner
        BookingService.remove_cached_slots(calendar_owner, date)
        BookingService.remove_cached_token(token)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

