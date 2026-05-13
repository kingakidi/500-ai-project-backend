from rest_framework import serializers
from django.contrib.auth import authenticate

from users.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES, default="user", required=False
    )

    class Meta:
        model = User
        fields = ["role", "first_name", "last_name", "email", "password"]
        extra_kwargs = {
            "email": {"required": True, "validators": []},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        role = attrs.get("role", "user")
        if role not in {"user", "superadmin"}:
            raise serializers.ValidationError({"role": "Invalid role."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role", "user")
        invited_by = validated_data.pop("invited_by", None)
        user = User.objects.create_user(
            password=password,
            role=role,
            invited_by=invited_by,
            **validated_data,
        )
        user.is_verified = True
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    code = serializers.CharField(max_length=4, min_length=4)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

