from enum import Enum

class MeetingStatus(Enum):
    BOOKED = 'booked'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    RESCHEDULED = 'rescheduled'
    PENDING = 'pending'

    @classmethod
    def choices(cls):
        return [(status.value, status.name.capitalize()) for status in cls]
