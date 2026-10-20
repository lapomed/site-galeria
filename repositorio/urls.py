from django.urls import path

from . import views

app_name = "repositorio"

urlpatterns = [
    path("", views.index, name="index"),
    path("pasta/<int:folder_id>/", views.browse, name="browse"),

    # Pastas
    path("pasta/criar/", views.folder_create, name="folder_create"),
    path("pasta/<int:pk>/renomear/", views.folder_rename, name="folder_rename"),
    path("pasta/<int:pk>/excluir/", views.folder_delete, name="folder_delete"),

    # Arquivos
    path("arquivo/<int:pk>/", views.file_detail, name="file_detail"),
    path("arquivo/<int:pk>/editar/", views.file_update, name="file_update"),
    path("arquivo/<int:pk>/excluir/", views.file_delete, name="file_delete"),
    path("arquivo/<int:pk>/baixar/", views.file_download, name="file_download"),

    # Upload multipart (JSON)
    path("upload/iniciar/", views.upload_init, name="upload_init"),
    path("upload/assinar/", views.upload_sign, name="upload_sign"),
    path("upload/concluir/", views.upload_complete, name="upload_complete"),
    path("upload/abortar/", views.upload_abort, name="upload_abort"),

    # Modelos de metadados
    path("modelos/", views.templates_list, name="templates"),
    path("modelos/novo/", views.template_form, name="template_create"),
    path("modelos/<int:pk>/editar/", views.template_form, name="template_edit"),
    path("modelos/<int:pk>/excluir/", views.template_delete, name="template_delete"),
]
