from django.urls import path

from .views import ChangePasswordView, UserDetailView, UsersView

app_name = "users"

urlpatterns = [
    path("", UsersView.as_view(), name="users"),
    path("/me/change-password", ChangePasswordView.as_view(), name="change-password"),
    path("/<uuid:user_id>", UserDetailView.as_view(), name="user-detail"),
]
