from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.pagination import ListPagination
from utils.response import APIResponse

from .models import User
from .serializers import ChangePasswordSerializer, UserSerializer, UserUpdateSerializer


class UsersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination

    @extend_schema(
        summary="List all users",
        description="Get a paginated list of all users",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of items per page",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search query to filter users by name or email",
            ),
        ],
        responses={200: UserSerializer(many=True)},
    )
    def get(self, request):
        from django.db.models import Q

        paginator = self.pagination_class()

        if request.user.is_superadmin():
            users = User.objects.filter(is_active=True).order_by("-created_at")
        else:
            users = User.objects.filter(
                Q(invited_by=request.user) | Q(id=request.user.id),
                is_active=True,
            ).order_by("-created_at")

        search_query = request.query_params.get("search", "").strip()
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        page = paginator.paginate_queryset(users, request)
        if page is not None:
            serializer = UserSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        serializer = UserSerializer(users, many=True, context={"request": request})
        return APIResponse.success("Users retrieved successfully", serializer.data)

    @extend_schema(
        summary="Update user profile",
        description="Update authenticated user's profile information",
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 400: None},
    )
    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user, context={"request": request}).data
            return APIResponse.success("User updated successfully", user_data)
        return APIResponse.validation_error("Validation failed", serializer.errors)

    @extend_schema(
        summary="Update user profile (partial)",
        description="Partially update authenticated user's profile information",
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 400: None},
    )
    def patch(self, request):
        return self.put(request)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change authenticated user's password",
        description=(
            "Change the password for the currently authenticated user. "
            "Validates the current password, checks that the new passwords match, "
            "and enforces basic strength rules (length and special character)."
        ),
        request=ChangePasswordSerializer,
        responses={200: None, 400: None},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success("Password updated successfully", None)
        return APIResponse.validation_error("Validation failed", serializer.errors)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get user by ID",
        description="Retrieve a specific user by their UUID. Non-superadmin users can only view users they invited.",
        responses={200: UserSerializer, 403: None, 404: None},
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        if not request.user.is_superadmin():
            if user.id == request.user.id:
                pass
            else:
                return APIResponse.forbidden(
                    "You can only view your own user."
                )

        serializer = UserSerializer(user, context={"request": request})
        return APIResponse.success("User retrieved successfully", serializer.data)

    @extend_schema(
        summary="Update user by ID",
        description="Update a specific user's information. Only super admin can update other users.",
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 400: None, 403: None, 404: None},
    )
    def put(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if not request.user.is_superadmin() and target_user.id != request.user.id:
            return APIResponse.forbidden("You cannot update other users.")

        serializer = UserUpdateSerializer(
            target_user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            role = serializer.validated_data.get("role")
            if role == "superadmin" and not request.user.is_superadmin():
                return APIResponse.forbidden(
                    "Only super admin can assign super admin role."
                )

            user = serializer.save()
            user_data = UserSerializer(user, context={"request": request}).data
            return APIResponse.success("User updated successfully", user_data)
        return APIResponse.validation_error("Validation failed", serializer.errors)

    @extend_schema(
        summary="Update user by ID (partial)",
        description="Partially update a specific user's information. Only super admin can update other users.",
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 400: None, 403: None, 404: None},
    )
    def patch(self, request, user_id):
        return self.put(request, user_id)

    @extend_schema(
        summary="Delete user by ID",
        description="Delete a specific user. Only super admin can delete users. Users cannot delete themselves.",
        responses={200: None, 403: None, 404: None},
    )
    def delete(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if not request.user.is_superadmin():
            return APIResponse.forbidden("Only super admin can delete users.")

        if target_user.id == request.user.id:
            return APIResponse.forbidden("You cannot delete your own account.")

        user_email = target_user.email
        target_user.is_active = False
        target_user.email = f"deleted_{target_user.id}@deleted.invalid"
        target_user.save(update_fields=["is_active", "email"])
        return APIResponse.success("User deleted successfully", None)
