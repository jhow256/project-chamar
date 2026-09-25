from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Consent, LoginAttempt, User


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ["ip_hash", "failures", "blocked_until", "last_failure_at", "updated_at"]
    readonly_fields = ["ip_hash", "failures", "last_failure_at", "updated_at"]
    search_fields = ["ip_hash"]
    actions = ["desbloquear"]

    @admin.action(description="Desbloquear IPs selecionados")
    def desbloquear(self, request, queryset):
        updated = queryset.update(failures=0, blocked_until=None)
        self.message_user(request, f"{updated} registro(s) desbloqueado(s).")

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "name", "role", "sector", "is_active", "is_staff", "is_superuser"]
    fieldsets = ((None, {"fields": ("email", "password")}), ("Dados", {"fields": ("name", "role", "sector", "anonymized_at")}), ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}), ("Datas", {"fields": ("last_login", "date_joined")}))
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "name", "role", "sector", "password1", "password2")}),)
    search_fields = ["email", "name"]
admin.site.register(Consent)
