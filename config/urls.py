from django.contrib import admin
from django.urls import path, include
from common.views.health import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("books.urls")),
    path("api/v1/", include("tenants.urls")),
    path("api/v1/payments/", include("payments.urls")),
    path("silk/", include("silk.urls", namespace="silk")),
]


handler404 = "common.exceptions.handler404"
handler500 = "common.exceptions.handler500"
