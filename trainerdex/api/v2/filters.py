import django_filters as filters

from trainerdex.fields import PogoDecimalField, PogoPositiveIntegerField
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
        fields=[
            (field.name, field.name)
            for field in Update._meta.fields
            if (
                isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
                and field.sortable is True
            )
            or field.name == "update_time"
        ]
    )

    class Meta:
        model = Update
        fields = ["trainer", "update_time"] + [
            field.name
            for field in Update._meta.fields
            if isinstance(field, (PogoDecimalField, PogoPositiveIntegerField))
            and field.sortable is True
        ]


class LeaderboardFilter(filters.FilterSet):
    nickname = filters.CharFilter(field_name="nicknames__nickname")

    class Meta:
        model = Trainer
        fields = ["nickname", "faction", "country", "communities"]
