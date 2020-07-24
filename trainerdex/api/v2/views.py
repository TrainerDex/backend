import logging
import math
from distutils.util import strtobool

from django.db.utils import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from rest_framework_extensions.mixins import NestedViewSetMixin

from trainerdex.api.v2.filters import (
    LeaderboardFilter,
    TrainerCodeFilter,
    TrainerFilter,
    UpdateFilter,
)
from trainerdex.api.v2.serializers import (
    LeaderboardSerializer,
    LeaderboardSerializerLegacy,
    NicknameSerializer,
    TrainerCodeSerializer,
    TrainerSerializer,
    UpdateSerializer,
)
from trainerdex.leaderboard import Leaderboard
from trainerdex.models import PresetTarget, Target, Trainer, TrainerCode, Update
from trainerdex.models import TrainerQuerySet, UpdateQuerySet

log = logging.getLogger("django.trainerdex")


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

    @action(detail=True, methods=["post"])
    def set_nickname(self, request, pk=None):
        """Set the nickname of the user"""
        user = self.get_object()
        serializer = NicknameSerializer(
            data={
                "user": user.pk,
                "nickname": request.data.get("nickname"),
                "active": request.data.get("active", True),
            }
        )
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
    filterset_class = LeaderboardFilter

    @property
    def get_serializer(self):
        if strtobool(self.request.query_params.get("legacy", "0")):
            return LeaderboardSerializerLegacy
        return LeaderboardSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        leaderboard = queryset.get_leaderboard(
            legacy_mode=strtobool(self.request.query_params.get("legacy", "0")),
            order_by=self.request.query_params.get("o", "total_xp"),
        )

        focus = self.request.query_params.get("focus", "")
        if focus.isnumeric():
            try:
                trnr_focus = Trainer.objects.get(pk=int(focus))
            except Trainer.DoesNotExist:
                return Response(
                    {"status": f"Unable to find a trainer with the ID of {focus}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            TRAINER_NOT_IN_SET = Response(
                {
                    "status": f"Trainer with id {focus} ({trnr_focus}) is not in this leaderboard.",
                    "profile-url": request.build_absolute_uri(
                        reverse("v2:trainer-detail", args=[trnr_focus.pk])
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            if isinstance(leaderboard, TrainerQuerySet):
                if not leaderboard.filter(pk=trnr_focus.pk).exists():
                    return TRAINER_NOT_IN_SET
            elif isinstance(leaderboard, UpdateQuerySet):
                if not leaderboard.filter(trainer=trnr_focus).exists():
                    return TRAINER_NOT_IN_SET

            for index, item in enumerate(leaderboard):
                if isinstance(item, Trainer):
                    pk = item.id
                elif isinstance(item, Update):
                    pk = item.trainer.id
                if pk == int(focus):
                    url = self.request.build_absolute_uri()
                    url = remove_query_param(url, "focus")
                    limit = max(
                        0,
                        int(
                            self.request.query_params.get(
                                "limit", api_settings.PAGE_SIZE
                            )
                        ),
                    )
                    url = replace_query_param(url, "limit", limit)
                    offset = max(0, index + 1 - math.ceil(limit / 2))
                    url = replace_query_param(url, "offset", offset)
                    return redirect(url)

        page = self.paginate_queryset(leaderboard)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get(self, request):
        return self.list(request)
