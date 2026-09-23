from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Consent, User


class UserSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "sector", "sector_name", "is_active", "is_staff", "anonymized_at", "created_at", "password"]
        read_only_fields = ["id", "sector_name", "is_staff", "anonymized_at", "created_at"]

    def validate_email(self, value):
        return value.strip().lower()

    def validate_sector(self, value):
        if value and not value.active:
            raise serializers.ValidationError("Selecione um setor ativo.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)
    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "sector", "sector_name", "created_at"]
        read_only_fields = ["id", "email", "role", "sector", "sector_name", "created_at"]


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = ["id", "policy_version", "accepted_at"]
        read_only_fields = ["id", "accepted_at"]
