import logging

from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from trainerdex.api.v2.filters import TrainerFilter, UpdateFiler
from trainerdex.api.v2.serializers import TrainerSerializer, UpdateSerializer
from trainerdex.models import Trainer, Update

log = logging.getLogger('django.trainerdex')

class TrainerViewSet(NestedViewSetMixin, ModelViewSet):
    """
    In the detail view, there is a field `updates`,
    this is limited to the 15 latest updates.
    It's recommended to use the `/api/v2/trainers/{pk}/updates/`
    url instead.
    
    For performance reasons, `updates` is excluded in the list view.
    """
    queryset = Trainer.objects.default_excludes()
    serializer_class = TrainerSerializer
    filterset_class = TrainerFilter


class UpdateViewSet(ModelViewSet):
    queryset = Update.objects.default_excludes()
    serializer_class = UpdateSerializer
    filterset_class = UpdateFiler


class NestedUpdateViewSet(NestedViewSetMixin, UpdateViewSet):
    pass
