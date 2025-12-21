from django.contrib import admin
from .models import Slide, Project, Artifact

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'active')
    list_editable = ('order', 'active')

class ArtifactInline(admin.TabularInline):
    model = Artifact
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArtifactInline]

@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('title', 'project')
    list_filter = ('project',)
