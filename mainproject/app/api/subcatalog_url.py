from django.urls import path
from ..views.catalog_option import add_subcatalog, change_subcatalog, delete_subcatalog


urlpatterns = [
    path("add/", add_subcatalog, name="add subcatalog"),
    path("change/", change_subcatalog, name="change subcatalog"),
    path("delete/", delete_subcatalog, name="delete subcatalog")
]