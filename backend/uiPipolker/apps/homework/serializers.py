from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from .models import Homework, HomeworkFile, HomeworkTask, Schedule, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажи название предмета.')
        duplicates = Subject.objects.filter(name__iexact=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError('Такой предмет уже есть.')
        return value


class ScheduleSerializer(serializers.ModelSerializer):
    subject_detail = SubjectSerializer(source='subject', read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'subject', 'subject_detail', 'weekday', 'lesson_number', 'is_online', 'room']
        read_only_fields = ['id']


class HomeworkTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkTask
        fields = ['id', 'text', 'order']
        read_only_fields = ['id']


class HomeworkFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkFile
        fields = ['id', 'file_name', 'download_url', 'file_type', 'uploaded_at']
        read_only_fields = fields

    def get_file_name(self, obj):
        return obj.file.name.rsplit('/', 1)[-1]

    def get_download_url(self, obj):
        return reverse('homework-file-download', kwargs={'pk': obj.pk})


class HomeworkFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        max_length=10,
    )

    def validate_files(self, files):
        allowed_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp',
            '.pdf', '.txt', '.docx', '.xlsx', '.pptx',
        }
        image_signatures = {
            '.jpg': lambda header: header.startswith(b'\xff\xd8\xff'),
            '.jpeg': lambda header: header.startswith(b'\xff\xd8\xff'),
            '.png': lambda header: header.startswith(b'\x89PNG\r\n\x1a\n'),
            '.gif': lambda header: header.startswith((b'GIF87a', b'GIF89a')),
            '.webp': lambda header: header[:4] == b'RIFF' and header[8:12] == b'WEBP',
        }
        total_size = 0

        for uploaded_file in files:
            extension = uploaded_file.name.rsplit('.', 1)[-1].lower()
            extension = f'.{extension}' if '.' in uploaded_file.name else ''
            if extension not in allowed_extensions:
                raise serializers.ValidationError(
                    'Разрешены изображения, PDF, TXT и документы DOCX, XLSX, PPTX.'
                )

            if uploaded_file.size > 15 * 1024 * 1024:
                raise serializers.ValidationError('Каждый файл должен быть не больше 15 МБ.')
            total_size += uploaded_file.size

            header = uploaded_file.read(16)
            uploaded_file.seek(0)
            if extension in image_signatures and not image_signatures[extension](header):
                raise serializers.ValidationError(
                    f'Файл «{uploaded_file.name}» не похож на изображение этого формата.'
                )
            if extension == '.pdf' and not header.startswith(b'%PDF-'):
                raise serializers.ValidationError(f'Файл «{uploaded_file.name}» не является PDF.')
            if extension in {'.docx', '.xlsx', '.pptx'} and not header.startswith(b'PK\x03\x04'):
                raise serializers.ValidationError(
                    f'Файл «{uploaded_file.name}» не является документом Office.'
                )
            if extension == '.txt' and b'\x00' in header:
                raise serializers.ValidationError(f'Файл «{uploaded_file.name}» не является текстовым.')

        if total_size > 50 * 1024 * 1024:
            raise serializers.ValidationError('Общий размер файлов не должен превышать 50 МБ.')
        return files


class HomeworkSerializer(serializers.ModelSerializer):
    subject_detail = SubjectSerializer(source='subject', read_only=True)
    tasks = HomeworkTaskSerializer(many=True, required=False)
    files = HomeworkFileSerializer(many=True, read_only=True)

    class Meta:
        model = Homework
        fields = [
            'id', 'subject', 'subject_detail', 'title', 'description', 'date',
            'tasks', 'files', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @transaction.atomic
    def create(self, validated_data):
        tasks = validated_data.pop('tasks', [])
        homework = Homework.objects.create(**validated_data)
        HomeworkTask.objects.bulk_create([
            HomeworkTask(homework=homework, text=task['text'], order=task.get('order', index))
            for index, task in enumerate(tasks)
        ])
        return homework

    @transaction.atomic
    def update(self, instance, validated_data):
        tasks = validated_data.pop('tasks', None)
        instance = super().update(instance, validated_data)
        if tasks is not None:
            instance.tasks.all().delete()
            HomeworkTask.objects.bulk_create([
                HomeworkTask(homework=instance, text=task['text'], order=task.get('order', index))
                for index, task in enumerate(tasks)
            ])
        return instance
