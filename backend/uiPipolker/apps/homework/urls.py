from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .auth_views import (
    LoginView,
    LogoutView,
    RegistrationInviteDetailView,
    RegistrationInviteListCreateView,
    RegistrationView,
    SessionRefreshView,
    CsrfTokenView,
)
from .views import (
    CurrentUserView,
    HomeworkFileDownloadView,
    HomeworkViewSet,
    ScheduleViewSet,
    SubjectViewSet,
)


router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='subject')
router.register('schedule', ScheduleViewSet, basename='schedule')
router.register('homework', HomeworkViewSet, basename='homework')

urlpatterns = [
    path('auth/csrf/', CsrfTokenView.as_view(), name='csrf-token'),
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/refresh/', SessionRefreshView.as_view(), name='session-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/invites/', RegistrationInviteListCreateView.as_view(), name='registration-invites'),
    path('auth/invites/<int:pk>/', RegistrationInviteDetailView.as_view(), name='registration-invite-delete'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('files/<int:pk>/download/', HomeworkFileDownloadView.as_view(), name='homework-file-download'),
    path('', include(router.urls)),
]
