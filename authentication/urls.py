from django.urls import path

from .views import (
    ForgotPasswordView,
    LoginView,
    RefreshTokenView,
    RegisterView,
    ResendOTPView,
    SetPasswordView,
    VerifyOTPView,
)

app_name = "authentication"

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("verify-otp", VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp", ResendOTPView.as_view(), name="resend-otp"),
    path("refresh", RefreshTokenView.as_view(), name="refresh"),
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("set-password", SetPasswordView.as_view(), name="set-password"),
]
