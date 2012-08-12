from django.contrib import admin

from warehouse.models import Project, Version, VersionFile


__all__ = ["ProjectAdmin", "VersionAdmin", "VersionFileAdmin"]


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


class VersionAdmin(admin.ModelAdmin):
    list_display = ["__unicode__", "project", "version", "summary", "author", "author_email", "maintainer", "maintainer_email", "created", "modified"]
    list_filter = ["created", "modified", "yanked"]
    raw_id_fields = ["project"]


class VersionFileAdmin(admin.ModelAdmin):
    list_display = ["version", "type", "python_version", "downloads", "comment", "created", "modified"]
    list_filter = ["type", "created", "modified"]
    search_fields = ["version__project__name", "filename"]
    raw_id_fields = ["version"]


admin.site.register(Project, ProjectAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(VersionFile, VersionFileAdmin)
