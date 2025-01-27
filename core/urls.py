from django.urls import path
from .views import UserListCreateView, UserDetailView
from .views import SetAvailabilityView
from .views import ListMeetingsView
# from .views import CreateMeetingView, ListMeetingsView, RescheduleMeetingView, UpdateMeetingStatusView
from .views import SearchAvailableSlotsView, BookAppointmentView

urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('set-availability/', SetAvailabilityView.as_view(), name='set-availability'),
    # path('meetings/', CreateMeetingView.as_view(), name='create-meeting'),

    # List all meetings for a calendar owner
    path('meetings/<int:user_id>/', ListMeetingsView.as_view(), name='list-meetings'),

    # Reschedule an existing meeting
    # path('meetings/<int:meeting_id>/reschedule/', RescheduleMeetingView.as_view(), name='reschedule-meeting'),

    # Update status of a meeting
    path('calendar/<int:user_id>/available-slots/', SearchAvailableSlotsView.as_view(), name='search-available-slots'),
    
    # Book Appointment
    path('calendar/book-appointment/', BookAppointmentView.as_view(), name='book-appointment'),
    # path('meetings/<int:meeting_id>/status/', UpdateMeetingStatusView.as_view(), name='update-meeting-status'),
]
