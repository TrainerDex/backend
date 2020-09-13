"""TrainerDex URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("trainerdex.api.urls")),
    path("oauth/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("", include("trainerdex.urls")),
]

if settings.INVITATIONS_INVITATION_ONLY:
    urlpatterns.append(
        path("accounts/invitations/", include("invitations.urls", namespace="invitations"))
    )

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
