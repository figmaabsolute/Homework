from pathlib import PurePosixPath

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Homework, HomeworkFile, Schedule, Subject
from .permissions import IsStaffOrReadOnly
from .serializers import (
    HomeworkFileSerializer,
    HomeworkFileUploadSerializer,
    HomeworkSerializer,
    ScheduleSerializer,
    SubjectSerializer,
)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'username': request.user.get_username(),
            'full_name': request.user.get_full_name(),
            'is_staff': request.user.is_staff,
        })


class HomeworkFileDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        attachment = get_object_or_404(HomeworkFile, pk=pk)
        try:
            stream = attachment.file.open('rb')
        except (FileNotFoundError, OSError) as exc:
            raise Http404('Файл не найден') from exc

        return FileResponse(
            stream,
            as_attachment=True,
            filename=PurePosixPath(attachment.file.name).name,
            content_type='application/octet-stream',
        )


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.select_related('subject').all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]


class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.select_related('subject').prefetch_related('tasks', 'files').all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]

    @action(
        detail=True,
        methods=['post'],
        url_path='files',
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_files(self, request, pk=None):
        homework = self.get_object()
        serializer = HomeworkFileUploadSerializer(
            data={'files': request.FILES.getlist('files')},
        )
        serializer.is_valid(raise_exception=True)

        attachments = [
            HomeworkFile.objects.create(
                homework=homework,
                file=uploaded_file,
                file_type=(
                    HomeworkFile.FileType.PHOTO
                    if uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
                    else HomeworkFile.FileType.OTHER
                ),
            )
            for uploaded_file in serializer.validated_data['files']
        ]
        return Response(
            HomeworkFileSerializer(attachments, many=True, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
