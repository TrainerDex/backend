import django_filters as filters

from trainerdex.fields import PogoDecimalField, PogoPositiveIntegerField
from trainerdex.models import Trainer, FriendCode, Update


class TrainerFilter(filters.FilterSet):
    codename = filters.CharFilter(field_name="codenames__codename")

    class Meta:
        model = Trainer
        fields = [
            "codename",
            "faction",
            "country",
        ]


class FriendCodeFilter(filters.FilterSet):
    trainer__codename = filters.CharFilter(field_name="trainer__codenames__codename")

    class Meta:
        model = FriendCode
        fields = [
            "trainer__codename",
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
    codename = filters.CharFilter(field_name="codenames__codename")

    class Meta:
        model = Trainer
        fields = ["codename", "faction", "country", "communities"]
