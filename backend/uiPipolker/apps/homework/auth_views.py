import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from .auth_serializers import (
    InviteIssueSerializer,
    InviteSummarySerializer,
    LoginSerializer,
    RegistrationSerializer,
)
from .invite_codes import digest_invite_code, make_invite_code
from .models import LoginSession, RegistrationInvite


SESSION_COOKIE_NAME = 'homework_session'
SESSION_LIFETIME = timedelta(days=30)


def _digest_session_secret(secret):
    return hashlib.sha256(secret.encode('utf-8')).hexdigest()


def _set_session_cookie(response, secret, expires_at):
    max_age = max(0, int((expires_at - timezone.now()).total_seconds()))
    response.set_cookie(
        SESSION_COOKIE_NAME,
        secret,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/api/v1/auth/',
    )
    return response


@method_decorator(csrf_protect, name='dispatch')
class CsrfTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'csrf_token': get_token(request)})


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        LoginSession.objects.filter(expires_at__lte=timezone.now()).delete()
        secret = secrets.token_urlsafe(48)
        expires_at = timezone.now() + SESSION_LIFETIME
        LoginSession.objects.create(
            user=serializer.user,
            token_digest=_digest_session_secret(secret),
            expires_at=expires_at,
        )
        return _set_session_cookie(
            Response(serializer.validated_data),
            secret,
            expires_at,
        )


@method_decorator(csrf_protect, name='dispatch')
class SessionRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        secret = request.COOKIES.get(SESSION_COOKIE_NAME)
        if not secret:
            return Response({'detail': 'Сеанс завершился. Войди снова.'}, status=status.HTTP_401_UNAUTHORIZED)

        session = LoginSession.objects.select_related('user').filter(
            token_digest=_digest_session_secret(secret),
            expires_at__gt=timezone.now(),
            user__is_active=True,
        ).first()
        if session is None:
            response = Response(
                {'detail': 'Сеанс завершился. Войди снова.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie(SESSION_COOKIE_NAME, path='/api/v1/auth/', samesite='Lax')
            return response

        session.last_used_at = timezone.now()
        session.save(update_fields=['last_used_at'])
        return Response({'access': str(AccessToken.for_user(session.user))})


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        secret = request.COOKIES.get(SESSION_COOKIE_NAME)
        if secret:
            LoginSession.objects.filter(token_digest=_digest_session_secret(secret)).delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            SESSION_COOKIE_NAME,
            path='/api/v1/auth/',
            samesite='Lax',
        )
        return response


@method_decorator(csrf_protect, name='dispatch')
class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'registration'

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'detail': 'Аккаунт создан. Теперь войдите в кабинет.', 'username': user.get_username()},
            status=status.HTTP_201_CREATED,
        )


class RegistrationInviteListCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        invites = RegistrationInvite.objects.select_related('used_by').all()
        data = InviteSummarySerializer(invites, many=True).data
        return Response(data)

    def post(self, request):
        serializer = InviteIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        code = make_invite_code()
        expires_at = timezone.now() + timedelta(hours=values['expires_in_hours'])

        invite = RegistrationInvite.objects.create(
            code_digest=digest_invite_code(code),
            label=values.get('label', '').strip(),
            created_by=request.user,
            expires_at=expires_at,
        )
        return Response(
            {
                'id': invite.pk,
                'code': code,
                'label': invite.label,
                'expires_at': invite.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )

class RegistrationInviteDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        invite = get_object_or_404(RegistrationInvite, pk=pk, used_at__isnull=True)
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
