from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from .models import Attachment, Category, Comment, Ticket, TicketHistory

EXTENSION_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".pdf": "application/pdf"}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "active", "created_at"]
        read_only_fields = ["id", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author_name", "text", "created_at"]
        read_only_fields = ["id", "author_name", "created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)
    detected_mime_type = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Attachment
        fields = ["id", "file", "detected_mime_type", "original_name", "mime_type", "size_bytes", "created_at", "download_url"]
        read_only_fields = ["id", "original_name", "mime_type", "size_bytes", "created_at", "download_url"]

    def validate_file(self, file):
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("O arquivo deve ter no máximo 5 MiB.")
        ext = Path(file.name).suffix.lower()
        expected_mime = EXTENSION_MIME.get(ext)
        if not expected_mime:
            raise serializers.ValidationError("Envie apenas PNG, JPG, JPEG ou PDF válido.")
        if file.content_type != expected_mime:
            raise serializers.ValidationError("O tipo de conteúdo informado não corresponde à extensão.")
        try:
            if ext == ".pdf":
                content = file.read()
                if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
                    raise serializers.ValidationError("O conteúdo do PDF é inválido ou está incompleto.")
                detected_mime = "application/pdf"
            else:
                image = Image.open(file)
                image.verify()
                detected_mime = Image.MIME.get(image.format)
                if detected_mime not in ("image/png", "image/jpeg"):
                    raise serializers.ValidationError("O conteúdo da imagem é inválido.")
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError("O conteúdo do arquivo é inválido.")
        finally:
            file.seek(0)
        if detected_mime != expected_mime:
            raise serializers.ValidationError("O conteúdo do arquivo não corresponde à extensão.")
        file.detected_mime_type = detected_mime
        return file

    def validate(self, attrs):
        file = attrs.get("file")
        if file:
            attrs["detected_mime_type"] = file.detected_mime_type
        return attrs

    def create(self, validated_data):
        validated_data.pop("detected_mime_type", None)
        return super().create(validated_data)

    def get_download_url(self, obj):
        return self.context["request"].build_absolute_uri(f"/api/v1/attachments/{obj.pk}/download/")


class HistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.name", read_only=True)

    class Meta:
        model = TicketHistory
        fields = ["id", "previous_status", "new_status", "changed_by_name", "details", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    urgency_perceived = serializers.ChoiceField(choices=Ticket.Priority.choices, required=True)
    requester_name = serializers.CharField(source="requester.name", read_only=True)
    technician_name = serializers.CharField(source="technician.name", read_only=True)
    sector_name = serializers.CharField(source="sector.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    equipment_type_name = serializers.CharField(source="equipment_type.name", read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "number", "title", "description", "status", "urgency_perceived", "priority", "requester_name", "technician", "technician_name", "sector", "sector_name", "category", "category_name", "equipment_type", "equipment_type_name", "solution", "rating", "created_at", "updated_at", "resolved_at", "deleted_at"]
        read_only_fields = ["id", "number", "status", "priority", "requester_name", "technician", "technician_name", "sector", "sector_name", "equipment_type_name", "solution", "rating", "created_at", "updated_at", "resolved_at", "deleted_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and (user.is_superuser or user.role in ("TECNICO", "ADMIN")):
            fields["priority"].read_only = False
        return fields

    def validate_category(self, value):
        if not value.active:
            raise serializers.ValidationError("Selecione uma categoria ativa.")
        return value

    def validate_equipment_type(self, value):
        if value and not value.active:
            raise serializers.ValidationError("Selecione um tipo de equipamento ativo.")
        return value

    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Descreva o problema com pelo menos 10 caracteres, sem incluir dados pessoais sensíveis.")
        return value
