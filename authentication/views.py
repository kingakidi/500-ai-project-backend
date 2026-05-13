from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import UserSerializer
from utils.response import APIResponse

from .models import OTP
from .serializers import (
    ResendOTPSerializer,
    ResetPasswordSerializer,
    SetPasswordSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    VerifyOTPSerializer,
)
from .utils import (
    OTP_TRY_COOLDOWN_SECONDS,
    allow_otp_action,
    send_invitation_email,
    send_otp_email,
)


class RegisterView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Register a new user (Super Admin Only)",
        description="Create a new user account. Only super admin can create users.",
        request=UserRegistrationSerializer,
        responses={201: UserSerializer, 400: None, 403: None, 409: None},
    )
    def post(self, request):
        if not request.user.is_superadmin():
            return APIResponse.forbidden("Only super admin can create new users.")

        serializer = UserRegistrationSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return APIResponse.validation_error(
                "Invalid or incomplete details", serializer.errors
            )

        email = serializer.validated_data.get("email")
        if email and User.objects.filter(email=email, is_active=True).exists():
            return APIResponse.duplicate("A user with this email already exists.")

        role = serializer.validated_data.get("role", "user")
        if role == "superadmin" and not request.user.is_superadmin():
            return APIResponse.forbidden("Only super admin can create super admin users.")

        raw_password = serializer.validated_data.get("password")

        try:
            user = serializer.save(invited_by=request.user)
        except IntegrityError:
            return APIResponse.duplicate("Email already exists")

        send_invitation_email(
            user=user,
            password=raw_password,
            invited_by=request.user,
        )

        user_data = UserSerializer(user, context={"request": request}).data
        return APIResponse.created("User registered successfully", user_data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login - Step 1",
        description="Authenticate user with email and password. An OTP code will be sent to your email for verification.",
        request=UserLoginSerializer,
        responses={200: None, 400: None, 401: None},
    )
    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            if not allow_otp_action(kind="send", purpose="login", email=user.email):
                return APIResponse.error(
                    message="Too many attempts. Please wait 1 minute and try again.",
                    data={"retry_after_seconds": OTP_TRY_COOLDOWN_SECONDS},
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            otp = OTP.create_otp(user=user, purpose="login", expiry_hours=24)
            send_otp_email(user, otp.code, purpose="login")

            return APIResponse.success(
                "Verification code sent to your email. Please check your inbox.",
                {"email": user.email},
            )
        return APIResponse.validation_error("Invalid credentials", serializer.errors)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh access token",
        description="Get a new access token using a refresh token",
        request={"type": "object", "properties": {"refresh": {"type": "string"}}},
        responses={200: None, 400: None},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return APIResponse.validation_error(
                "Validation failed", {"refresh": ["This field is required."]}
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return APIResponse.success(
                "Token refreshed successfully",
                {"access_token": access_token, "refresh_token": str(refresh)},
            )
        except Exception as e:
            return APIResponse.validation_error(
                "Invalid refresh token", {"refresh": ["Invalid or expired token."]}
            )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify OTP - Step 2",
        description="Verify the one-time code sent to your email and complete login or password reset",
        request=VerifyOTPSerializer,
        responses={200: UserSerializer, 400: None, 401: None},
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error("Validation failed", serializer.errors)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        purpose = request.data.get("purpose", "login")

        if not allow_otp_action(kind="try", purpose=purpose, email=email):
            return APIResponse.error(
                message="Too many attempts. Please wait 1 minute and try again.",
                data={"retry_after_seconds": OTP_TRY_COOLDOWN_SECONDS},
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse.not_found("User not found")

        otp = (
            OTP.objects.filter(user=user, code=code, purpose=purpose, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return APIResponse.validation_error(
                "Invalid or expired verification code",
                {"code": ["The verification code is invalid or has expired."]},
            )

        if not otp.is_valid():
            return APIResponse.validation_error(
                "Verification code has expired",
                {
                    "code": [
                        "The verification code has expired. Please request a new one."
                    ]
                },
            )

        otp.mark_as_used()

        if purpose == "forgot-password":
            return APIResponse.success(
                "OTP verified successfully. You can now set a new password.",
                {"email": user.email, "verified": True},
            )

        login(request, user)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        user_data = UserSerializer(user, context={"request": request}).data
        user_data["access_token"] = access_token
        user_data["refresh_token"] = refresh_token

        return APIResponse.success("Login successful", user_data)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend OTP",
        description="Resend a new one-time verification code to your email",
        request=ResendOTPSerializer,
        responses={200: None, 400: None, 404: None},
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error("Validation failed", serializer.errors)

        email = serializer.validated_data["email"]
        purpose = request.data.get("purpose", "login")

        if not allow_otp_action(kind="send", purpose=purpose, email=email):
            return APIResponse.error(
                message="Too many attempts. Please wait 1 minute and try again.",
                data={"retry_after_seconds": OTP_TRY_COOLDOWN_SECONDS},
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse.not_found("User not found")

        otp = OTP.create_otp(user=user, purpose=purpose, expiry_hours=24)
        send_otp_email(user, otp.code, purpose=purpose)

        return APIResponse.success(
            "A new verification code has been sent to your email.",
            {"email": user.email},
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Forgot password - Step 1",
        description="Request password reset. An OTP code will be sent to your email for verification.",
        request=ResetPasswordSerializer,
        responses={200: None, 400: None, 404: None},
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error("Validation failed", serializer.errors)

        email = serializer.validated_data["email"]

        if not allow_otp_action(kind="send", purpose="forgot-password", email=email):
            return APIResponse.error(
                message="Too many attempts. Please wait 1 minute and try again.",
                data={"retry_after_seconds": OTP_TRY_COOLDOWN_SECONDS},
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse.success(
                "If an account exists with this email, a verification code has been sent.",
                {"email": email},
            )

        otp = OTP.create_otp(user=user, purpose="forgot-password", expiry_hours=24)
        send_otp_email(user, otp.code, purpose="forgot-password")

        return APIResponse.success(
            "OTP code has been sent to your email. Please check your inbox.",
            {"email": user.email},
        )


class SetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Set new password",
        description="Set a new password after OTP verification for forgot password flow",
        request=SetPasswordSerializer,
        responses={200: None, 400: None, 404: None},
    )
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error("Validation failed", serializer.errors)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse.not_found("User not found")

        otp = (
            OTP.objects.filter(
                user=user, code=code, purpose="forgot-password", is_used=True
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return APIResponse.validation_error(
                "Invalid verification code",
                {"code": ["Please verify OTP first before setting password."]},
            )

        from datetime import timedelta

        from django.utils import timezone

        if otp.updated_at < timezone.now() - timedelta(hours=1):
            return APIResponse.validation_error(
                "Verification expired",
                {
                    "code": [
                        "OTP verification has expired. Please start the process again."
                    ]
                },
            )

        user.set_password(password)
        user.save()

        return APIResponse.success(
            "Password has been reset successfully. A notification email has been sent.",
            {"email": user.email},
        )
