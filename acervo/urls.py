from django.urls import path

from . import views

app_name = "acervo"

urlpatterns = [
    path("", views.index, name="index"),
    path("atlas.geojson", views.atlas, name="atlas"),
    path("item/<slug:slug>/", views.item, name="item"),
    path("item/<slug:slug>/geo.json", views.item_geo, name="item_geo"),
    path("item/<slug:slug>/tabela.json", views.item_table, name="item_table"),
    path("item/<slug:slug>/raw", views.item_raw, name="item_raw"),
    path("item/<slug:slug>/download", views.item_download, name="item_download"),
]
