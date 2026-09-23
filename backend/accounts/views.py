import hashlib
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiResponse, OpenApiTypes, extend_schema
from audit.services import audit
from core.permissions import IsAdmin, IsTechnician
from .models import Consent, User
from .serializers import ConsentSerializer, ProfileSerializer, UserSerializer

COOKIE = "refresh_token"


def enforce_csrf(request):
    reason = CsrfViewMiddleware(lambda _request: None).process_view(request._request, None, (), {})
    if reason is not None:
        return Response(
            {
                "erro": {
                    "codigo": "CSRF_INVALIDO",
                    "mensagem": "Token CSRF ausente ou inválido. Envie o cookie CSRF e o cabeçalho X-CSRFToken correspondentes.",
                    "detalhes": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def set_refresh(response, token):
    response.set_cookie(COOKIE, str(token), max_age=7 * 86400, httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite="Strict", path="/api/v1/auth/")


@extend_schema(request={"email": OpenApiTypes.EMAIL, "password": OpenApiTypes.STR}, responses={200: OpenApiTypes.OBJECT})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def login(request):
    login.throttle_scope = "login"
    user = authenticate(request, email=request.data.get("email", "").lower(), password=request.data.get("password", ""))
    if not user or not user.is_active:
        return Response({"erro": {"codigo": "CREDENCIAIS_INVALIDAS", "mensagem": "E-mail ou senha inválidos.", "detalhes": {}}}, status=401)
    refresh = RefreshToken.for_user(user)
    get_token(request)
    response = Response({"access": str(refresh.access_token), "user": ProfileSerializer(user).data})
    set_refresh(response, refresh)
    audit(request, "LOGIN", "auth")
    return response


@extend_schema(request=None, responses={200: OpenApiTypes.OBJECT})
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    csrf_error = enforce_csrf(request)
    if csrf_error:
        return csrf_error
    raw = request.COOKIES.get(COOKIE)
    if not raw:
        return Response({"erro": {"codigo": "REFRESH_AUSENTE", "mensagem": "Sessão de renovação não encontrada.", "detalhes": {}}}, status=401)
    try:
        old = RefreshToken(raw)
        old.blacklist()
        user = User.objects.get(pk=old["user_id"], is_active=True)
        new = RefreshToken.for_user(user)
    except (TokenError, User.DoesNotExist):
        return Response({"erro": {"codigo": "REFRESH_INVALIDO", "mensagem": "Sessão expirada ou inválida.", "detalhes": {}}}, status=401)
    response = Response({"access": str(new.access_token)})
    set_refresh(response, new)
    return response


@extend_schema(request=None, responses={204: OpenApiResponse(description="Sessão encerrada.")})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    csrf_error = enforce_csrf(request)
    if csrf_error:
        return csrf_error
    raw = request.COOKIES.get(COOKIE)
    if raw:
        try:
            RefreshToken(raw).blacklist()
        except TokenError:
            pass
    response = Response(status=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE, path="/api/v1/auth/", samesite="Strict")
    if request.user.is_authenticated:
        audit(request, "LOGOUT", "auth")
    return response


@extend_schema(request={"email": OpenApiTypes.EMAIL}, responses={200: OpenApiTypes.OBJECT})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset(request):
    password_reset.throttle_scope = "password_reset"
    email = request.data.get("email", "").lower()
    user = User.objects.filter(email=email, is_active=True).first()
    if user:
        token = default_token_generator.make_token(user)
        send_mail(
            "Recuperação de senha",
            f"Identificador: {user.pk}\nToken de recuperação: {token}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    return Response({"mensagem": "Se o e-mail estiver cadastrado, as instruções de recuperação serão enviadas."})


@extend_schema(request={"user_id": OpenApiTypes.UUID, "token": OpenApiTypes.STR, "new_password": OpenApiTypes.STR}, responses={200: OpenApiTypes.OBJECT})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset_confirm(request):
    password_reset_confirm.throttle_scope = "password_reset"
    user = User.objects.filter(pk=request.data.get("user_id"), is_active=True).first()
    token = request.data.get("token", "")
    new_password = request.data.get("new_password", "")
    if not user or not default_token_generator.check_token(user, token):
        return Response(
            {"erro": {"codigo": "TOKEN_INVALIDO", "mensagem": "Token de recuperação inválido ou expirado.", "detalhes": {}}},
            status=400,
        )
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    try:
        validate_password(new_password, user)
    except DjangoValidationError as exc:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"new_password": list(exc.messages)}) from exc
    user.set_password(new_password)
    user.save(update_fields=["password"])
    audit(request, "PASSWORD_RESET_COMPLETED", f"user:{user.pk}")
    return Response({"mensagem": "Senha redefinida com sucesso."})


@extend_schema(request=ProfileSerializer, responses=ProfileSerializer)
@api_view(["GET", "PATCH"])
def me(request):
    if request.method == "PATCH":
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        audit(request, "PROFILE_UPDATED", f"user:{request.user.pk}")
        return Response(serializer.data)
    return Response(ProfileSerializer(request.user).data)


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
def data_export(request):
    user = request.user
    data = {"user": ProfileSerializer(user).data, "consents": ConsentSerializer(user.consents.all(), many=True).data,
            "tickets": list(user.requested_tickets.values("number", "title", "description", "status", "urgency_perceived", "priority", "solution", "rating", "created_at")),
            "comments": list(user.comments.values("ticket__number", "text", "created_at"))}
    audit(request, "PERSONAL_DATA_EXPORTED", f"user:{user.pk}")
    return Response(data)


@extend_schema(request=ConsentSerializer, responses={201: ConsentSerializer})
@api_view(["POST"])
def consent(request):
    serializer = ConsentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    audit(request, "CONSENT_RECORDED", f"user:{request.user.pk}", {"version": serializer.data["policy_version"]})
    return Response(serializer.data, status=201)


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@permission_classes([AllowAny])
def privacy_policy(request):
    return Response({
        "version": "1.0.0",
        "title": "Política de Privacidade do Chamar",
        "summary": (
            "Coletamos nome, e-mail, setor e informações necessárias aos chamados para prestar suporte, "
            "controlar acesso, manter segurança e produzir estatísticas. Não informe senhas, CPF, dados de saúde "
            "ou outros dados pessoais sensíveis nos chamados. Você pode corrigir e exportar seus dados; "
            "solicitações de anonimização são executadas pelo administrador conforme a política de retenção."
        ),
        "sharing": "Os dados não são compartilhados com terceiros na demonstração.",
        "contact": settings.DEFAULT_FROM_EMAIL,
    })


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@permission_classes([IsTechnician])
def technicians(request):
    users = User.objects.filter(role=User.Role.TECHNICIAN, is_active=True).order_by("name")
    return Response([{"id": str(user.id), "name": user.name} for user in users])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("sector").all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "sector", "is_active"]
    search_fields = ["name", "email"]
    ordering_fields = ["name", "email", "created_at"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        user = serializer.save()
        audit(self.request, "USER_CREATED", f"user:{user.pk}")

    def perform_update(self, serializer):
        user = serializer.save()
        safe_fields = sorted(set(serializer.validated_data) - {"password"})
        audit(self.request, "USER_UPDATED", f"user:{user.pk}", {"campos": safe_fields})

    @action(detail=True, methods=["post"])
    def anonymize(self, request, pk=None):
        user = self.get_object()
        if user.is_active:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"user": "O usuário deve estar inativo antes da anonimização."})
        digest = hashlib.sha256(f"{settings.SECRET_KEY}:{user.pk}".encode()).hexdigest()
        user.name = "Usuário anonimizado"
        user.email = f"anonimizado-{digest}@invalid.local"
        user.first_name = user.last_name = ""
        user.sector = None
        user.anonymized_at = timezone.now()
        user.set_unusable_password()
        user.save()
        audit(request, "USER_ANONYMIZED", f"user:{user.pk}")
        return Response(UserSerializer(user).data)
