from django.urls import include, path
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path(
        "openapi",
        get_schema_view(
            title="TrainerDex",
            version="2.0",
            url="https://trainerdex.app/api/v2/",
            urlconf="trainerdex.api.v2.urls",
        ),
        name="openapi-schema",
    ),
    path("v1/", include("trainerdex.api.v1.urls", namespace="v1")),
    path("v2/", include("trainerdex.api.v2.urls", namespace="v2")),
]
