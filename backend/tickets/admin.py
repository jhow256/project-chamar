from django.contrib import admin

from .models import Attachment, Category, Comment, Ticket, TicketHistory


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "status", "urgency_perceived", "priority", "equipment_type", "requester", "technician", "created_at"]
    list_filter = ["status", "urgency_perceived", "priority", "sector", "category", "equipment_type"]
    search_fields = ["number", "title", "description"]
    readonly_fields = ["number", "created_at", "updated_at", "resolved_at", "deleted_at"]

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Attachment)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ["ticket", "previous_status", "new_status", "changed_by", "created_at"]
    readonly_fields = ["ticket", "previous_status", "new_status", "changed_by", "details", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
