from django.urls import path
from ..views.notify_option import check_notify, get_notify, seen_notify


urlpatterns = [
    path("check/", check_notify),
    path("get/", get_notify),
    path("seen/", seen_notify)
]