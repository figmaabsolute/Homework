from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.homework.models import Homework


class Command(BaseCommand):
    help = 'Удаляет задания, срок сдачи которых прошёл больше указанного числа дней назад.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=10,
            help='Сколько дней хранить задания после срока сдачи (по умолчанию: 10).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать число заданий, которые будут удалены.',
        )

    def handle(self, *args, **options):
        retention_days = options['days']
        if retention_days < 1:
            raise CommandError('--days должен быть не меньше 1.')

        cutoff_date = timezone.localdate() - timedelta(days=retention_days)
        expired_homework = Homework.objects.filter(date__lt=cutoff_date).prefetch_related('files')
        homework_count = expired_homework.count()
        if not homework_count:
            self.stdout.write(self.style.SUCCESS('Старых заданий нет.'))
            return

        if options['dry_run']:
            self.stdout.write(
                f'Найдено заданий для удаления: {homework_count} '
                f'(срок сдачи раньше {cutoff_date:%d.%m.%Y}).'
            )
            return

        stored_files = [
            (attachment.file.storage, attachment.file.name)
            for homework in expired_homework
            for attachment in homework.files.all()
            if attachment.file
        ]

        failed_files = []
        for storage, name in stored_files:
            try:
                storage.delete(name)
            except Exception as exc:
                failed_files.append((name, exc))

        if failed_files:
            self.stderr.write(
                self.style.WARNING(
                    f'Не удалось удалить файлов: {len(failed_files)}. '
                    'Записи заданий оставлены; команда безопасно повторяется.'
                )
            )
            for name, exc in failed_files:
                self.stderr.write(f'  {name}: {exc}')
            raise CommandError('Очистка остановлена, чтобы не удалить записи с недоступными файлами.')

        with transaction.atomic():
            expired_homework.delete()

        self.stdout.write(self.style.SUCCESS(f'Удалено заданий: {homework_count}.'))
