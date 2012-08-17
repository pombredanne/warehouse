from django.contrib import admin

from warehouse.models import UserAgent, Download


class UserAgentAdmin(admin.ModelAdmin):
    list_display = ["agent"]
    search_fields = ["agent"]


class DownloadAdmin(admin.ModelAdmin):
    list_display = ["datetime", "project", "version", "filename", "downloads"]
    raw_id_fields = ["user_agent"]


admin.site.register(UserAgent, UserAgentAdmin)
admin.site.register(Download, DownloadAdmin)
