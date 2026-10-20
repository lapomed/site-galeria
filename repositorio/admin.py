from django.contrib import admin

from .models import RepoFolder, MetadataTemplate, RepoFile


@admin.register(RepoFolder)
class RepoFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_by", "created_at")
    list_filter = ("parent",)
    search_fields = ("name",)


@admin.register(MetadataTemplate)
class MetadataTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(RepoFile)
class RepoFileAdmin(admin.ModelAdmin):
    list_display = ("name", "folder", "status", "human_size", "content_type", "created_at")
    list_filter = ("status", "folder")
    search_fields = ("name", "original_filename", "object_key")
    readonly_fields = ("object_key", "size", "created_at", "updated_at")
