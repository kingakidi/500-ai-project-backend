from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FacultyViewSet

app_name = "faculty"

router = DefaultRouter()
router.register(r"faculties", FacultyViewSet, basename="faculties")

urlpatterns = [
    path("", include(router.urls)),
]

