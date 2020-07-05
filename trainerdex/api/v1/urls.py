from django.urls import path

from trainerdex.api.v1.views import SocialAccountViewSet, TrainerViewSet, UpdateViewSet, UserViewSet

app_name = 'trainerdex.api:v1'

urlpatterns = [
    # /trainers/
    path('trainers/', TrainerViewSet.as_view({'get': 'list'})),
    path('trainers/<int:pk>/', TrainerViewSet.as_view({'get': 'retrieve'})),
    path('trainers/<int:pk>/updates/', UpdateViewSet.as_view({'get': 'list'})),
    path('trainers/<int:pk>/updates/latest/', UpdateViewSet.as_view({'get': 'latest'})),
    path('trainers/<int:pk>/updates/<uuid:uuid>/', UpdateViewSet.as_view({'get': 'retrieve'})),
    # /users/
    path('users/', UserViewSet.as_view({'get': 'list'})),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve'})),
    path('users/social/', SocialAccountViewSet.as_view({'get': 'list'})),
]
