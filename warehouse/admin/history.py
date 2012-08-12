from django.contrib import admin

from warehouse.models import Event


__all__ = ["EventAdmin"]


class EventAdmin(admin.ModelAdmin):
    list_display = ["created", "user", "project", "version", "filename", "data"]
    list_filter = ["created"]
    search_fields = ["user__username", "project", "version", "filename"]


admin.site.register(Event, EventAdmin)
