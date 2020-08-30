import django_filters as filters

from trainerdex.models import Trainer, TrainerCode, Update


class TrainerFilter(filters.FilterSet):
    nickname = filters.CharFilter(field_name="nicknames__nickname")

    class Meta:
        model = Trainer
        fields = [
            "nickname",
            "faction",
            "country",
        ]


class TrainerCodeFilter(filters.FilterSet):
    trainer__nickname = filters.CharFilter(field_name="trainer__nicknames__nickname")

    class Meta:
        model = TrainerCode
        fields = [
            "trainer__nickname",
            "trainer__faction",
            "trainer__country",
        ]


class UpdateFilter(filters.FilterSet):
    update_time = filters.IsoDateTimeFromToRangeFilter()

    o = filters.OrderingFilter(
        fields=[(x, x) for x, y in Update.field_metadata().items() if y.get("sortable") == True]
        + [
            ("update_time", "update_time"),
        ]
    )

    class Meta:
        model = Update
        fields = ["trainer", "update_time"] + [
            x for x, y in Update.field_metadata().items() if y.get("sortable") == True
        ]


class LeaderboardFilter(filters.FilterSet):
    nickname = filters.CharFilter(field_name="nicknames__nickname")

    class Meta:
        model = Trainer
        fields = ["nickname", "faction", "country", "communities"]
