from django.urls import path
from ..views.catalog_option import get_catalogs, change_catalog, delete_catalog, add_catalog, get_one_catalog


urlpatterns = [
    path("get/", get_catalogs, name="get catalogs"),
    path("change/", change_catalog, name="change catalogs"),
    path("delete/", delete_catalog, name="get catalogs"),
    path("add/", add_catalog, name="add catalogs"),
    path("get_one/", get_one_catalog)
]