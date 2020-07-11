from typing import Iterator

from django.db.models import Max, F, Window, Subquery
from django.db.models.functions import DenseRank

from trainerdex.models import Trainer, TrainerQuerySet, Update, UpdateQuerySet


class LeaderboardEntry:
    def __init__(self, *args, **kwargs) -> None:
        self.trainer = Trainer.objects.only('pk', 'username', 'faction').get(pk=kwargs.get('trainer', kwargs.get('pk')))
        self.value = kwargs.get('value')
        self.datetime = kwargs.get('datetime')
        self.rank = kwargs.get('rank')


class Leaderboard:
    def __init__(self, legacy_mode: bool = False, order_by: str = 'total_xp', queryset: TrainerQuerySet = Trainer.objects.all()) -> None:
        self.order_by = order_by
        self.legacy = legacy_mode
        self.__manager = LegacyLeaderboardManager() if self.legacy else LeaderboardManager()
        self.queryset = queryset
        self.__query = self.__manager.get_queryset(o=self.order_by, q=self.queryset)
    
    def __iter__(self) -> Iterator[LeaderboardEntry]:
        for entry in self.query.values('pk' if self.legacy else 'trainer', 'rank', 'value', 'datetime'):
            yield LeaderboardEntry(**entry)


class LeaderboardManager:
    def get_queryset(self, o: str, q: TrainerQuerySet) -> UpdateQuerySet:
        assert isinstance(q, TrainerQuerySet)
        return Update.objects.filter(pk__in=Subquery(
                Update.objects.default_excludes()
                .filter(trainer__in=q)
                .annotate(value=F(o))
                .exclude(value__isnull=True)
                .order_by('trainer', '-value')
                .distinct('trainer')
                .values('pk')
            )).annotate(value=F(o), datetime=F('update_time')) \
            .annotate(rank=Window(expression=DenseRank(), order_by=F('value').desc())) \
            .order_by('rank', '-value', 'datetime')


class LegacyLeaderboardManager:
    def get_queryset(self, o: str, q: TrainerQuerySet) -> TrainerQuerySet:
        assert isinstance(q, TrainerQuerySet)
        return q.default_excludes() \
            .prefetch_related('updates') \
            .annotate(value=Max(f'updates__{o}'), datetime=Max('updates__update_time')) \
            .exclude(value__isnull=True) \
            .annotate(rank=Window(expression=DenseRank(), order_by=F('value').desc())) \
            .order_by('rank', '-value', 'datetime')
