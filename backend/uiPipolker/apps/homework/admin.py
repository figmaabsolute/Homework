from django.contrib import admin

from .models import Homework, HomeworkFile, HomeworkTask, LoginSession, RegistrationInvite, Schedule, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('weekday', 'lesson_number', 'subject')
    list_filter = ('weekday', 'subject')
    search_fields = ('subject__name',)
    ordering = ('weekday', 'lesson_number')


class HomeworkTaskInline(admin.TabularInline):
    model = HomeworkTask
    extra = 1
    ordering = ('order',)


class HomeworkFileInline(admin.TabularInline):
    model = HomeworkFile
    extra = 1
    fields = ('file', 'file_type')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'subject',
        'title',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'subject',
        'date',
    )

    search_fields = (
        'title',
        'description',
        'subject__name',
    )

    ordering = (
        '-date',
        'subject',
    )

    date_hierarchy = 'date'

    inlines = (
        HomeworkTaskInline,
        HomeworkFileInline,
    )


@admin.register(RegistrationInvite)
class RegistrationInviteAdmin(admin.ModelAdmin):
    list_display = ('label', 'created_by', 'created_at', 'expires_at', 'used_at', 'used_by')
    list_filter = ('created_at', 'expires_at', 'used_at')
    search_fields = ('label', 'created_by__username', 'used_by__username')
    readonly_fields = ('label', 'created_by', 'created_at', 'expires_at', 'used_at', 'used_by')
    exclude = ('code_digest',)

    def has_add_permission(self, request):
        return False


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'last_used_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'token_digest', 'created_at', 'last_used_at', 'expires_at')
    exclude = ('token_digest',)

    def has_add_permission(self, request):
        return False
