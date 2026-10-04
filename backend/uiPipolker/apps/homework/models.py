from django.conf import settings
from django.db import models
from django.utils import timezone


class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Предмет'
    )

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Schedule(models.Model):
    class WeekDay(models.IntegerChoices):
        MONDAY = 0, 'Понедельник'
        TUESDAY = 1, 'Вторник'
        WEDNESDAY = 2, 'Среда'
        THURSDAY = 3, 'Четверг'
        FRIDAY = 4, 'Пятница'

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='schedule_items',
        verbose_name='Предмет'
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WeekDay.choices,
        verbose_name='День недели'
    )

    lesson_number = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Номер пары'
    )

    is_online = models.BooleanField(
        default=False,
        verbose_name='Онлайн занятие'
    )

    room = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Кабинет / Аудитория'
    )

    class Meta:
        verbose_name = 'Занятие в расписании'
        verbose_name_plural = 'Расписание'
        ordering = ['weekday', 'lesson_number']

    def __str__(self):
        format_type = "Онлайн" if self.is_online else f"Пара №{self.lesson_number}"
        return f'{self.get_weekday_display()} — {format_type}: {self.subject}'


class Homework(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Предмет'
    )

    title = models.CharField(
        max_length=500,
        verbose_name='Название'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    date = models.DateField(
        verbose_name='Дата выполнения'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата изменения'
    )

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-date', 'subject']

    def __str__(self):
        return f'{self.subject} — {self.title}'


class HomeworkTask(models.Model):
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Домашнее задание'
    )

    text = models.TextField(
        verbose_name='Текст задания'
    )

    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    class Meta:
        verbose_name = 'Пункт задания'
        verbose_name_plural = 'Пункты заданий'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:50]


class HomeworkFile(models.Model):
    class FileType(models.TextChoices):
        PHOTO = 'photo', 'Фотография'
        SOLUTION = 'solution', 'Решение'
        OTHER = 'other', 'Другое'

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Домашнее задание'
    )

    file = models.FileField(
        upload_to='homework/',
        verbose_name='Файл'
    )

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.PHOTO,
        verbose_name='Тип файла'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )

    class Meta:
        verbose_name = 'Прикрепленный файл'
        verbose_name_plural = 'Прикрепленные файлы'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.homework} — {self.file.name}'


class RegistrationInvite(models.Model):
    code_digest = models.CharField(max_length=64, unique=True, editable=False)
    label = models.CharField(max_length=100, blank=True, verbose_name='Для кого')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='issued_registration_invites',
        verbose_name='Создал',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    expires_at = models.DateTimeField(verbose_name='Истекает')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='Использовано')
    used_by = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registration_invite',
        verbose_name='Зарегистрировался',
    )

    class Meta:
        verbose_name = 'Приглашение на регистрацию'
        verbose_name_plural = 'Приглашения на регистрацию'
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    def __str__(self):
        return self.label or f'Приглашение №{self.pk}'


class LoginSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='homework_sessions',
    )
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Сеанс кабинета'
        verbose_name_plural = 'Сеансы кабинета'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — до {self.expires_at:%d.%m.%Y}'
