from rest_framework.permissions import BasePermission


class IsTechnician(BasePermission):
    message = "Acesso permitido somente para técnicos e administradores."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and (user.is_superuser or user.role in ("TECNICO", "ADMIN"))
        )


class IsAdmin(BasePermission):
    message = "Acesso permitido somente para administradores."

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and (user.is_superuser or user.role == "ADMIN"))


class IsOwnerOrTechnician(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user.is_superuser
            or user.role in ("TECNICO", "ADMIN")
            or obj.requester_id == user.id
        )
