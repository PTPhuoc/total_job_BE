from django.urls import path, include

urlpatterns = [
    path("job/", include("app.api.job_url")),
    path("auth/", include("app.api.auth_url")),
    path("catalog/", include("app.api.catalog_url")),
    path("crawl/", include("app.api.crawl_url")),
    path("subcatalog/", include("app.api.subcatalog_url")),
    path("company/", include("app.api.company_url")),
    path("account/", include("app.api.account_url")),
    path("statistical/", include("app.api.statistical_url")),
    path("admin/", include("app.api.admin_url")),
    path("notify/", include("app.api.notify_url"))
]
