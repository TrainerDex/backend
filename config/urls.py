from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('trainerdex.api.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
