from typing import Union

from django.db.models import F, Max, Subquery, Window
from django.db.models.functions import DenseRank

from trainerdex.fields import PogoDecimalField, PogoPositiveIntegerField
from trainerdex.models import Trainer, Update
from trainerdex.models import TrainerQuerySet, UpdateQuerySet


class Leaderboard:
    def __init__(
        self,
        legacy_mode: bool = False,
        order_by: str = "total_xp",
        queryset: TrainerQuerySet = Trainer.objects.all(),
    ) -> None:
        self.order_by = order_by
        self.legacy = legacy_mode
        self.__manager = LegacyLeaderboardManager() if self.legacy else LeaderboardManager()
        self.queryset = queryset
        self._query = self.__manager.get_queryset(o=self.order_by, q=self.queryset)

    @property
    def objects(self) -> Union[UpdateQuerySet, TrainerQuerySet]:
        if self.legacy:
            return self._query.annotate(trainer=F("pk"))
        else:
            return self._query

    def __str__(self) -> str:
        if self.legacy:
            mode = "Legacy "
        else:
            mode = ""
        return f"{mode}Leaderboard with {self.objects.count()} entries"

    def __repr__(self) -> str:
        return self.__str__()


class LeaderboardManager:
    def get_queryset(self, o: str, q: TrainerQuerySet) -> UpdateQuerySet:
        assert isinstance(q, TrainerQuerySet)
        return (
            Update.objects.filter(
                pk__in=Subquery(
                    Update.objects.default_excludes()
                    .filter(trainer__in=q)
                    .annotate(value=F(o))
                    .exclude(value__isnull=True)
                    .order_by("trainer", "-value")
                    .distinct("trainer")
                    .values("pk")
                )
            )
            .prefetch_related("trainer", "trainer__faction", "data_source")
            .annotate(value=F(o), datetime=F("update_time"))
            .annotate(rank=Window(expression=DenseRank(), order_by=F("value").desc()))
            .order_by("rank", "-value", "datetime")
        )


class LegacyLeaderboardManager:
    def get_queryset(self, o: str, q: TrainerQuerySet) -> TrainerQuerySet:
        assert isinstance(q, TrainerQuerySet)
        return (
            q.default_excludes()
            .prefetch_related("updates", "faction")
            .annotate(
                **{
                    f"extra_max__{field.name}": Max(f"updates__{field.name}")
                    for field in Update._meta.fields
                    if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
                    and field.reversable is False
                }
            )
            .annotate(value=Max(f"updates__{o}"), datetime=Max("updates__update_time"))
            .exclude(value__isnull=True)
            .annotate(rank=Window(expression=DenseRank(), order_by=F("value").desc()))
            .order_by("rank", "-value", "datetime")
        )
