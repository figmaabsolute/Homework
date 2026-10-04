from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .invite_codes import digest_invite_code
from .models import RegistrationInvite


class LoginSerializer(TokenObtainPairSerializer):
    """Return a short-lived access token; the browser session is issued separately."""

    def validate(self, attrs):
        tokens = super().validate(attrs)
        tokens.pop('refresh', None)
        return tokens


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    invite_code = serializers.CharField(max_length=100, write_only=True, trim_whitespace=True)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        user_model = get_user_model()
        normalized = user_model.normalize_username(value)
        if user_model.objects.filter(**{user_model.USERNAME_FIELD: normalized}).exists():
            raise serializers.ValidationError('Этот логин уже занят.')
        return normalized

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})

        user_model = get_user_model()
        candidate = user_model(
            **{
                user_model.USERNAME_FIELD: attrs['username'],
                'first_name': attrs.get('first_name', ''),
                'last_name': attrs.get('last_name', ''),
            }
        )
        try:
            password_validation.validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages}) from exc

        digest = digest_invite_code(attrs['invite_code'])
        invite = RegistrationInvite.objects.filter(code_digest=digest).first()
        if invite is None or invite.used_at is not None or invite.expires_at <= timezone.now():
            raise serializers.ValidationError({'invite_code': 'Код приглашения недействителен или уже использован.'})

        attrs['invite'] = invite
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        invite = validated_data.pop('invite')
        invite_code = validated_data.pop('invite_code')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        user_model = get_user_model()

        user = user_model.objects.create_user(password=password, **validated_data)
        now = timezone.now()
        updated = RegistrationInvite.objects.filter(
            pk=invite.pk,
            code_digest=digest_invite_code(invite_code),
            used_at__isnull=True,
            expires_at__gt=now,
        ).update(used_at=now, used_by=user)
        if updated != 1:
            raise serializers.ValidationError({'invite_code': 'Код приглашения уже использован.'})
        return user


class InviteIssueSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=100, required=False, allow_blank=True)
    expires_in_hours = serializers.IntegerField(default=72, min_value=1, max_value=720)


class InviteSummarySerializer(serializers.ModelSerializer):
    used_by = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = RegistrationInvite
        fields = ['id', 'label', 'created_at', 'expires_at', 'used_at', 'used_by', 'status']

    def get_used_by(self, invite):
        return invite.used_by.get_username() if invite.used_by else None

    def get_status(self, invite):
        if invite.used_at:
            return 'used'
        if invite.is_expired:
            return 'expired'
        return 'active'
