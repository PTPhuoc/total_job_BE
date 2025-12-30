from django.urls import path
from ..views.statistical_option import get_catalyst_chart

urlpatterns = [
    path("info_chart/", get_catalyst_chart)
]