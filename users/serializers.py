from rest_framework import serializers

from .models import User

class InvitedBySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = ["id", "email", "first_name", "last_name"]


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = ["role", "first_name", "last_name", "email", "password"]
        extra_kwargs = {
            "email": {"required": False},
        }

    def validate(self, attrs):
        role = attrs.get("role") or (self.instance and self.instance.role)
        if role not in {"user", "superadmin"}:
            raise serializers.ValidationError({"role": "Invalid role."})
        return attrs

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password and password.strip():
            instance.set_password(password)

        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context.get("request").user
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Current password is incorrect."}
            )

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        if len(new_password) < 8:
            raise serializers.ValidationError(
                {"new_password": "Password must be at least 8 characters long."}
            )

        if all(ch.isalnum() for ch in new_password):
            raise serializers.ValidationError(
                {
                    "new_password": "Password must contain at least one special character."
                }
            )

        return attrs

    def save(self, **kwargs):
        user = self.context.get("request").user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return user


class UserSerializer(serializers.ModelSerializer):
    invited_by = InvitedBySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "role",
            "first_name",
            "last_name",
            "email",
            "is_verified",
            "invited_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_verified",
            "invited_by",
            "created_at",
            "updated_at",
        ]
