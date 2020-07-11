from django.db.models import Max, F, Window, Subquery
from django.db.models.functions import DenseRank

from trainerdex.models import Trainer, Update


class LeaderboardEntry:
    def __init__(self, *args, **kwargs):
        self.trainer = Trainer.objects.only('pk', 'username', 'faction').get(pk=kwargs.get('trainer', kwargs.get('pk')))
        self.value = kwargs.get('value')
        self.datetime = kwargs.get('datetime')
        self.rank = kwargs.get('rank')


class Leaderboard:
    def __init__(self, legacy_mode: bool = False, order_by: str = 'total_xp'):
        self.order_by = order_by
        self.legacy = legacy_mode
        self.__manager = LegacyLeaderboardManager() if self.legacy else LeaderboardManager()
        self.query = self.__manager.get_queryset(order_by=self.order_by)
    
    def __iter__(self):
        for entry in self.query.values('pk' if self.legacy else 'trainer', 'rank', 'value', 'datetime'):
            yield LeaderboardEntry(**entry)


class LeaderboardManager:
    def get_queryset(cls, order_by):
        return Update.objects.filter(pk__in=Subquery(
                Update.objects.default_excludes() \
                .annotate(value=F(order_by)) \
                .exclude(value__isnull=True) \
                .order_by('trainer','-value') \
                .distinct('trainer') \
                .values('pk')
            )).annotate(value=F(order_by), datetime=F('update_time')) \
            .annotate(rank=Window(expression=DenseRank(), order_by=F('value').desc())) \
            .order_by('rank', '-value', 'datetime')


class LegacyLeaderboardManager:
    def get_queryset(cls, order_by):
        return Trainer.objects.default_excludes() \
            .prefetch_related('updates') \
            .annotate(value=Max(f'updates__{order_by}'), datetime=Max('updates__update_time')) \
            .exclude(value__isnull=True) \
            .annotate(rank=Window(expression=DenseRank(), order_by=F('value').desc())) \
            .order_by('rank', '-value', 'datetime')
