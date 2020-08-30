import datetime
import logging

from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.serializers import SerializerMetaclass
from rest_framework import status

from trainerdex.api.v1.serializers import (
    BriefUpdateSerializer,
    DetailedUpdateSerializer,
    SocialAllAuthSerializer,
    TrainerSerializer,
    UserSerializer,
)
from trainerdex.models import Trainer, Update
from trainerdex.models import TrainerQuerySet, UpdateQuerySet

log = logging.getLogger("django.trainerdex")


class UserViewSet(ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    queryset = Trainer.objects.default_excludes().exclude(old_id__isnull=True)


class TrainerViewSet(ReadOnlyModelViewSet):
    serializer_class = TrainerSerializer

    def get_queryset(self) -> TrainerQuerySet:
        """
        Optionally restricts the returned trainers by name or team,
        by filtering against a `q` or `t` query parameter in the URL,
        where `t` is the faction id and `q` is a trainers nickname.
        Possible faction id's are 0-3 in this order: grey,blue,red,yellow.
        """
        queryset = Trainer.objects.default_excludes()
        nickname = self.request.query_params.get("q")
        faction = self.request.query_params.get("t")
        if nickname:
            queryset = queryset.filter(nickname__nickname=nickname)
        if faction:
            queryset = queryset.filter(faction__pk=faction)
        return queryset


class UpdateViewSet(ReadOnlyModelViewSet):
    queryset = Update.objects.default_excludes()

    def get_serializer_class(self) -> SerializerMetaclass:
        if self.action == "list" or not self.request.query_params.get("detail", True):
            return BriefUpdateSerializer
        return DetailedUpdateSerializer

    def get_trainer(self, pk: int) -> Trainer:
        try:
            obj = Trainer.objects.get(old_id=pk)
        except Trainer.DoesNotExist:
            raise Http404

        if not obj.is_active:
            raise Http404

        return obj

    def get_object(self, pk: int, uuid) -> Update:
        try:
            obj = self.queryset.get(trainer=self.get_trainer(pk), uuid=uuid)
        except Update.DoesNotExist:
            raise Http404

        return obj

    def list(self, request, pk: int) -> Response:
        queryset = self.queryset.filter(trainer=self.get_trainer(pk))
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def detail(self, request, pk: int, uuid) -> Response:
        update = self.get_object(trainer=pk, uuid=uuid)
        serializer = self.get_serializer_class()(update)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def latest(self, request, pk: int) -> Response:
        try:
            obj = self.queryset.filter(trainer=self.get_trainer(pk)).latest("update_time")
        except Update.DoesNotExist:
            raise Http404

        serializer = self.get_serializer_class()(obj)
        return Response(serializer.data)


class SocialAccountViewSet(ReadOnlyModelViewSet):
    model = SocialAccount.objects.all()
    serializer_class = SocialAllAuthSerializer

    def list(self, request) -> Response:
        """
        provider:
            str, required
            options are 'discord', 'facebook', 'google', 'twitter'
        uid:
            int
            Social ID, supports a comma seperated list
        user:
            int
            New TrainerDex User IDs (all users have this)
        trainer:
            int
            Old TrainerDex Trainer IDs (not all users have this)
        """
        provider = str(self.request.query_params.get("provider"))
        uid = self.request.query_params.get("uid")
        user = self.request.query_params.get("user")
        trainer = int(self.request.query_params.get("trainer"))

        query = SocialAccount.objects.exclude(user__is_active=False).filter(
            provider=request.GET.get("provider")
        )
        if uid:
            query = query.filter(uid__in=uid.split(","))
        if user:
            query = query.filter(user__in=user.split(","))
        if trainer:
            query = query.filter(user__trainer__id=trainer)
        if not any({uid, user, trainer}):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer_class()(query, many=True)
        return Response(serializer.data)
