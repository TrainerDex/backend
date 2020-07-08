from rest_framework import routers

from trainerdex.api.v2.views import TrainerViewSet, UpdateViewSet

app_name = 'trainerdex.api:v2'

router = routers.DefaultRouter()
router.register(r'trainers', TrainerViewSet)
router.register(r'updates', UpdateViewSet)

urlpatterns = router.urls
