import logging

from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from trainerdex.api.v2.filters import TrainerFilter, TrainerCodeFilter, UpdateFilter
from trainerdex.api.v2.serializers import TrainerSerializer, TrainerCodeSerializer, UpdateSerializer, NicknameSerializer, LeaderboardSerializer, LeaderboardSerializerLegacy
from trainerdex.leaderboard import Leaderboard
from trainerdex.models import Trainer, TrainerCode, Update, Target, PresetTarget

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
    
    @action(detail=True, methods=['post'])
    def set_nickname(self, request, pk=None):
        """Set the nickname of the user"""
        user = self.get_object()
        serializer = NicknameSerializer(data={'user': user.pk, 'nickname': request.data.get('nickname'), 'active': request.data.get('active', True)})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UpdateViewSet(ModelViewSet):
    queryset = Update.objects.default_excludes()
    serializer_class = UpdateSerializer
    filterset_class = UpdateFilter


class NestedUpdateViewSet(NestedViewSetMixin, UpdateViewSet):
    pass


class TrainerCodeViewSet(ModelViewSet):
    queryset = TrainerCode.objects.all()
    serializer_class = TrainerCodeSerializer
    filterset_class = TrainerCodeFilter


class LeaderboardView(ListAPIView):
    """View the leaderboard, init"""
    queryset = Trainer.objects.default_excludes()
    
    @property
    def get_serializer(self):
        if self.request.query_params.get('legacy', False):
            return LeaderboardSerializerLegacy
        return LeaderboardSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        leaderboard = queryset.get_leaderboard(
            legacy_mode=self.request.query_params.get('legacy', False),
            order_by=self.request.query_params.get('o', 'total_xp'),
        )
        
        page = self.paginate_queryset(leaderboard)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get(self, request):
        return self.list(request)
