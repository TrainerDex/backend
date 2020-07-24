from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, npgettext_lazy, pgettext_lazy

from django_countries.fields import CountryField
from timezone_field import TimeZoneField

from trainerdex.leaderboard import Leaderboard
from trainerdex.models import Trainer


class Community(models.Model):
    handle = models.SlugField(
        primary_key=True,
        verbose_name=pgettext_lazy("community__handle__title", "Handle"),
        help_text=pgettext_lazy(
            "community__handle__help",
            "Once you set this, it cannot be changed. Pick carefully as this will be the identifier to find your community leaderboard.",
        ),
    )
    language = models.CharField(
        default=settings.LANGUAGE_CODE,
        choices=settings.LANGUAGES,
        max_length=len(max(dict(settings.LANGUAGES).keys(), key=len)),
        verbose_name=_("language"),
    )
    timezone = TimeZoneField(default=settings.TIME_ZONE, verbose_name=_("timezone"))
    country = CountryField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("community__country__title", "country"),
        help_text=pgettext_lazy(
            "community__country__help", "Where your community is based"
        ),
    )

    name = models.CharField(
        max_length=70,
        verbose_name=pgettext_lazy("community__name__title", "name"),
        help_text=pgettext_lazy("community__name__help", "Max 70 characters"),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("community__description__title", "description"),
        help_text=pgettext_lazy(
            "community__description__help",
            "What makes your community unique? What are you about?",
        ),
    )

    can_see = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("community__can_see__title", "Publicly Viewable"),
        help_text=pgettext_lazy(
            "community__can_see__help",
            "Default: False\nTurn this on to share your community with the world.",
        ),
    )
    can_join = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("community__can_join__title", "Publicly Joinable"),
        help_text=pgettext_lazy(
            "community__can_join__title",
            "Default: False\nTurn this on to make your community free to join. No invites required.",
        ),
    )

    members = models.ManyToManyField(
        Trainer, blank=True, related_query_name="communities",
    )

    def country_flag(self):
        return self.country.unicode_flag

    country_flag.short_description = country.verbose_name

    def get_leaderboard(self, legacy_mode: bool = False, order_by: str = "total_xp"):
        return self.members.default_excludes().get_leaderboard(legacy_mode, order_by)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = npgettext_lazy("community__title", "community", "communities", 1)
        verbose_name_plural = npgettext_lazy(
            "community__title", "community", "communities", 2
        )
