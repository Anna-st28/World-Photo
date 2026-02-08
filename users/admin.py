from django.contrib import admin
from .models import PhotographerProfile, Photo, News, SupportRequest


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'subject')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'message', 'admin_response')
    readonly_fields = ('user', 'message', 'created_at')
    fieldsets = (
        ('Информация о запросе', {
            'fields': ('user', 'created_at', 'status')
        }),
        ('Сообщение', {
            'fields': ('subject', 'message')
        }),
        ('Ответ', {
            'fields': ('admin_response',)
        }),
    )


admin.site.register(PhotographerProfile)
admin.site.register(Photo)
admin.site.register(News)
