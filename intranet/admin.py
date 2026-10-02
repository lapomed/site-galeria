from django.contrib import admin
from .models import Task, IntranetAccess


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "due_date", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("title", "description")
    filter_horizontal = ("assignees",)


@admin.register(IntranetAccess)
class IntranetAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "is_manager", "menu_eventos", "menu_tarefas",
                    "menu_calendario", "menu_equipe")
    list_filter = ("is_manager",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
