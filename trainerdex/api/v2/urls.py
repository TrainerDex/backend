from django.urls import path

from rest_framework_extensions import routers

from trainerdex.api.v2.views import (
    LeaderboardView,
    NestedUpdateViewSet,
    TrainerCodeViewSet,
    TrainerViewSet,
    UpdateViewSet,
)

app_name = "trainerdex.api:v2"

router = routers.ExtendedSimpleRouter()
router.register(r"trainers", TrainerViewSet, basename="trainer").register(
    r"updates",
    NestedUpdateViewSet,
    basename="trainers-update",
    parents_query_lookups=["trainer"],
)

router.register(r"trainer-code", TrainerCodeViewSet)
router.register(r"updates", UpdateViewSet)

urlpatterns = [
    path("leaderboard/", LeaderboardView.as_view()),
]

urlpatterns += router.urls
