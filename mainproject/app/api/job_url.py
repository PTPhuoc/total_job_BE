from django.urls import path
from ..views.job_option import (
    get_job, get_job_desc, get_catalysis, search_job, get_one_job,
    get_require_job, check_content, save_job, check_save_job, get_save_job
)

urlpatterns = [
    path("get/", get_job, name="get_job"),
    path("get_one/", get_one_job, name="get_one_job"),
    path("get_desc/", get_job_desc, name="get_detail_job"),
    path("get_require/", get_require_job, name="get_require_job"),
    path("get_catalysis/", get_catalysis, name="get_catalysis"),
    path("search/", search_job, name="search_job"),
    path("check_content/", check_content, name="check_content"),
    path("save/", save_job, name="save_job"),
    path("check_save/", check_save_job, name="check_save_job"),
    path("get_save/", get_save_job, name="get_save_job"),
]
