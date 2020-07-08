import logging

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from trainerdex.api.v2.serializers import TrainerSerializer, UpdateSerializer
from trainerdex.models import Trainer, Update

log = logging.getLogger('django.trainerdex')

class TrainerViewSet(ModelViewSet):
    serializer_class = TrainerSerializer
    queryset = Trainer.objects.default_excludes()

class UpdateViewSet(ModelViewSet):
    serializer_class = UpdateSerializer
    queryset = Update.objects.default_excludes()
