from django.urls import path
from ..views.admin_option import get_account, change_password_by_admin, delete_account, delete_job, delete_company


urlpatterns = [
    path("get_account/", get_account),
    path("change_password/", change_password_by_admin),
    path("delete_account/", delete_account),
    path("delete_job/", delete_job),
    path("delete_company/", delete_company),
]