from rest_framework import pagination

class PostPaginator(pagination.PageNumberPagination):
    page_size = 20