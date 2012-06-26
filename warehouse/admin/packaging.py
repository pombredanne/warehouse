from django.contrib import admin

from warehouse.models import Project


__all__ = ["ProjectAdmin"]


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "normalized", "downloads", "created", "modified"]
    list_filter = ["created", "modified"]
    search_fields = ["name", "normalized"]
    readonly_fields = ["normalized"]

    fieldsets = (
        (None, {
            "fields": ["name", "normalized", "downloads", "uris"],

        }),
    )


admin.site.register(Project, ProjectAdmin)
