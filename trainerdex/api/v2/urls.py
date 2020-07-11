from rest_framework_extensions import routers

from trainerdex.api.v2.views import TrainerViewSet, UpdateViewSet, NestedUpdateViewSet

app_name = 'trainerdex.api:v2'

router = routers.ExtendedSimpleRouter()
router.register(r'trainers', TrainerViewSet, basename='trainer').register(
    r'updates',
    NestedUpdateViewSet,
    basename='trainers-update',
    parents_query_lookups=['trainer']
    )
router.register(r'updates', UpdateViewSet)

urlpatterns = router.urls
