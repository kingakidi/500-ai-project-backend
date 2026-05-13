from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseRegistrationViewSet

app_name = "course_registrations"

router = DefaultRouter()
router.register(
    r"course-registrations", CourseRegistrationViewSet, basename="course-registrations"
)

urlpatterns = [
    path("", include(router.urls)),
]

