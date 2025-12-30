from django.urls import path
from ..views.crawldata import active_craw_topcv, check_crawl


urlpatterns = [
    path("topcv/", active_craw_topcv, name="active craw topcv"),
    path("check/", check_crawl, name="check catalogs")
]