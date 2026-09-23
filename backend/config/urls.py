from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts import views as account_views
from audit.views import AuditLogViewSet
from core.views import health
from organization.views import EquipmentTypeViewSet, SectorViewSet
from tickets.views import CategoryViewSet, TicketViewSet, download_attachment

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")
router.register("categories", CategoryViewSet)
router.register("sectors", SectorViewSet)
router.register("equipment-types", EquipmentTypeViewSet)
router.register("users", account_views.UserViewSet)
router.register("audit/logs", AuditLogViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/v1/auth/login/", account_views.login),
    path("api/v1/auth/refresh/", account_views.refresh),
    path("api/v1/auth/logout/", account_views.logout),
    path("api/v1/auth/password-reset/", account_views.password_reset),
    path("api/v1/auth/password-reset/confirm/", account_views.password_reset_confirm),
    path("api/v1/auth/me/", account_views.me),
    path("api/v1/technicians/", account_views.technicians),
    path("api/v1/me/data-export/", account_views.data_export),
    path("api/v1/privacy/policy/", account_views.privacy_policy),
    path("api/v1/privacy/consent/", account_views.consent),
    path("api/v1/attachments/<int:pk>/download/", download_attachment),
    path("api/v1/dashboard/", include("dashboard.urls")),
    path("api/v1/health/", health),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
