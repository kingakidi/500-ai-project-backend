from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ListPagination(PageNumberPagination):
    rest_framework_settings = getattr(settings, "REST_FRAMEWORK", {})
    page_size = rest_framework_settings.get("PAGE_SIZE", 20)
    page_size_query_param = rest_framework_settings.get(
        "PAGE_SIZE_QUERY_PARAM", "page_size"
    )
    max_page_size = rest_framework_settings.get("MAX_PAGE_SIZE", 100)

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "data": {
                    "data": data,
                    "meta": {
                        "count": self.page.paginator.count,
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link(),
                        "current_page": self.page.number,
                        "total_pages": self.page.paginator.num_pages,
                        "page_size": self.page_size,
                    },
                },
                "error": {},
                "message": "Success",
            }
        )
