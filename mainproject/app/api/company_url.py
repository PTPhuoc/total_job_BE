from django.urls import path
from ..views.company_option import get_one_company, get_company

urlpatterns = [
    path("get_one/", get_one_company, name="get one company"),
    path("search/", get_company)
]