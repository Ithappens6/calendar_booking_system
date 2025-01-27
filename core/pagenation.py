from rest_framework.pagination import PageNumberPagination

class MeetingPagination(PageNumberPagination):
    page_size = 10  # Number of meetings per page (default)
    page_size_query_param = 'page_size'  # Allow client to set custom page size
    max_page_size = 100  # Maximum allowed page size
