from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StudentViewSet

app_name = "students"

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="students")

urlpatterns = [
    path("", include(router.urls)),
]

